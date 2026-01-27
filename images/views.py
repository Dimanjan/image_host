import json
import os
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .forms import CategoryForm, ImageUploadForm, ProductForm, StoreForm
from .models import Category, Image, Product, Store


def register_view(request):
    """User registration view"""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f"Account created for {username}!")
                return redirect("store_list")
    else:
        form = UserCreationForm()
    return render(request, "images/register.html", {"form": form})


def login_view(request):
    """User login view"""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect("store_list")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "images/login.html")


@login_required
def store_list(request):
    """List all stores for the current user"""
    stores = Store.objects.filter(user=request.user)
    return render(request, "images/store_list.html", {"stores": stores})


@login_required
def store_create(request):
    """Create a new store and its associated tables"""
    if request.method == "POST":
        # Added request.FILES to handle logo upload
        form = StoreForm(request.POST, request.FILES)
        if form.is_valid():
            store = form.save(commit=False)
            store.user = request.user
            store.save()

            # Create store-specific tables
            from .store_tables import create_store_tables

            try:
                create_store_tables(store.id)
                messages.success(
                    request,
                    f'Store "{store.name}" created successfully with its own tables!',
                )
            except Exception as e:
                messages.error(
                    request, f"Store created but table creation failed: {str(e)}"
                )

            return redirect("store_detail", store_id=store.id)
    else:
        form = StoreForm()
    return render(request, "images/store_form.html", {"form": form, "action": "Create"})


@login_required
def store_detail(request, store_id):
    """View store details with categories and all images"""
    from django.utils.text import slugify

    from .store_helpers import StoreCategory, StoreImage, StoreProduct

    store = get_object_or_404(Store, id=store_id, user=request.user)

    # Get categories from store-specific table
    categories = StoreCategory.objects(store_id).all()

    # Create a dictionary of category_id -> product count for template
    category_product_counts = {}
    for category in categories:
        category_products = StoreProduct.objects(store_id).filter(
            category_id=category.id
        )
        category_product_counts[category.id] = len(category_products)

    # Collect all images organized by category and product
    images_by_category = []
    for category in categories:
        # Get products for this category
        products = StoreProduct.objects(store_id).filter(category_id=category.id)
        products_data = []
        for product in products:
            # Get images for this product
            images = StoreImage.objects(store_id).filter(product_id=product.id)
            images_data = []
            for image in images:
                image_url = request.build_absolute_uri(
                    reverse(
                        "image_view",
                        kwargs={
                            "store_name": slugify(store.name),
                            "category_name": slugify(category.name),
                            "product_name": slugify(product.name),
                            "image_code": image.image_code,
                        },
                    )
                )
                images_data.append(
                    {
                        "id": image.id,
                        "name": image.name,
                        "image_code": image.image_code,
                        "url": image_url,
                    }
                )
            if images_data:
                products_data.append(
                    {
                        "product": product,
                        "images": images_data,
                    }
                )
        if products_data:
            images_by_category.append(
                {
                    "category": category,
                    "products": products_data,
                }
            )

    return render(
        request,
        "images/store_detail.html",
        {
            "store": store,
            "categories": categories,
            "category_product_counts": category_product_counts,
            "images_by_category": images_by_category,
        },
    )


@login_required
def category_create(request, store_id):
    """Create a new category"""
    from .store_helpers import StoreCategory

    store = get_object_or_404(Store, id=store_id, user=request.user)
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = StoreCategory.objects(store_id).create(
                name=form.cleaned_data["name"]
            )
            messages.success(
                request, f'Category "{category.name}" created successfully!'
            )
            return redirect("store_detail", store_id=store.id)
    else:
        form = CategoryForm()
    return render(
        request,
        "images/category_form.html",
        {"form": form, "store": store, "action": "Create"},
    )


@login_required
def category_update(request, store_id, category_id):
    """Update an existing category"""
    from .store_helpers import StoreCategory

    store = get_object_or_404(Store, id=store_id, user=request.user)
    category = StoreCategory.objects(store_id).get(id=category_id)

    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            category.name = form.cleaned_data["name"]
            category.save()
            messages.success(
                request, f'Category "{category.name}" updated successfully!'
            )
            return redirect(
                "category_detail", store_id=store_id, category_id=category.id
            )
    else:
        form = CategoryForm(initial={"name": category.name})

    return render(
        request,
        "images/category_form.html",
        {"form": form, "store": store, "action": "Update"},
    )


@login_required
def category_detail(request, store_id, category_id):
    """View category details with products"""
    from .store_helpers import StoreCategory, StoreProduct

    store = get_object_or_404(Store, id=store_id, user=request.user)
    category = StoreCategory.objects(store_id).get(id=category_id)
    products = StoreProduct.objects(store_id).filter(category_id=category_id)
    return render(
        request,
        "images/category_detail.html",
        {
            "category": category,
            "store": store,
            "products": products,
        },
    )


@login_required
def product_create(request, store_id, category_id):
    """Create a new product"""
    from .store_helpers import StoreCategory, StoreProduct

    store = get_object_or_404(Store, id=store_id, user=request.user)
    category = StoreCategory.objects(store_id).get(id=category_id)

    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = StoreProduct.objects(store_id).create(
                category=category,
                name=form.cleaned_data["name"],
                marked_price=form.cleaned_data.get("marked_price"),
                min_discounted_price=form.cleaned_data.get("min_discounted_price"),
                description=form.cleaned_data.get("description", "").strip(),
            )
            messages.success(request, f'Product "{product.name}" created successfully!')
            return redirect("product_detail", store_id=store_id, product_id=product.id)
    else:
        form = ProductForm()
    return render(
        request,
        "images/product_form.html",
        {"form": form, "category": category, "store": store, "action": "Create"},
    )


@login_required
def product_update(request, store_id, product_id):
    """Update an existing product"""
    from .store_helpers import StoreCategory, StoreProduct

    store = get_object_or_404(Store, id=store_id, user=request.user)
    product = StoreProduct.objects(store_id).get(id=product_id)
    category = product.category

    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product.name = form.cleaned_data["name"]
            product.marked_price = form.cleaned_data.get("marked_price")
            product.min_discounted_price = form.cleaned_data.get("min_discounted_price")
            product.description = form.cleaned_data.get("description", "").strip()
            product.save()
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect("product_detail", store_id=store_id, product_id=product.id)
    else:
        initial_data = {
            "name": product.name,
            "marked_price": product.marked_price,
            "min_discounted_price": product.min_discounted_price,
            "description": product.description,
        }
        form = ProductForm(initial=initial_data)

    return render(
        request,
        "images/product_form.html",
        {"form": form, "category": category, "store": store, "action": "Update"},
    )


@login_required
def product_detail(request, store_id, product_id):
    """View product details and upload images"""
    from .store_helpers import StoreCategory, StoreImage, StoreProduct

    store = get_object_or_404(Store, id=store_id, user=request.user)
    product = StoreProduct.objects(store_id).get(id=product_id)
    category = product.category
    images = StoreImage.objects(store_id).filter(product_id=product_id)

    if request.method == "POST":
        # Check if it's a multiple upload
        if "image_files" in request.FILES:
            # Handle multiple image uploads
            files = request.FILES.getlist("image_files")
            labels = request.POST.getlist("image_labels", [])
            image_codes = request.POST.getlist("image_codes", [])

            uploaded_count = 0
            for idx, file in enumerate(files):
                # Get label for this image (use filename without extension if no label provided)
                if idx < len(labels) and labels[idx].strip():
                    label = labels[idx].strip()
                else:
                    # Use filename without extension as fallback
                    label = os.path.splitext(file.name)[0]

                # Get image code (use provided code or empty string for auto-generation)
                image_code = ""
                if idx < len(image_codes) and image_codes[idx].strip():
                    # Clean the provided image code
                    code = image_codes[idx].strip().lower()
                    code = re.sub(r"[^a-z0-9_]", "", code)
                    code = re.sub(r"_+", "_", code)
                    code = code.strip("_")
                    if code:
                        image_code = code

                # Create image instance using store-specific helper
                image = StoreImage.objects(store_id).create(
                    product=product,
                    name=label,
                    image_file=file,
                    image_code=image_code,  # Will be auto-generated if empty
                )
                uploaded_count += 1

            if uploaded_count > 0:
                messages.success(
                    request, f"Successfully uploaded {uploaded_count} image(s)!"
                )

        # Check for URL uploads
        image_urls = request.POST.getlist("image_urls")
        if image_urls:
            url_labels = request.POST.getlist("url_labels", [])
            url_codes = request.POST.getlist("url_codes", [])
            
            url_count = 0
            for idx, url in enumerate(image_urls):
                if not url.strip():
                    continue
                    
                # Get label
                if idx < len(url_labels) and url_labels[idx].strip():
                    label = url_labels[idx].strip()
                else:
                    # Use last part of URL as label fallback
                    import os
                    from urllib.parse import urlparse
                    path = urlparse(url).path
                    label = os.path.basename(path) or "Image from URL"

                # Get code
                image_code = ""
                if idx < len(url_codes) and url_codes[idx].strip():
                    code = url_codes[idx].strip().lower()
                    code = re.sub(r"[^a-z0-9_]", "", code)
                    code = re.sub(r"_+", "_", code)
                    code = code.strip("_")
                    if code:
                        image_code = code
                
                # Create image instance
                StoreImage.objects(store_id).create(
                    product=product,
                    name=label,
                    url=url.strip(),
                    image_code=image_code
                )
                url_count += 1
            
            if url_count > 0:
                 messages.success(
                    request, f"Successfully added {url_count} image URL(s)!"
                )
            
        if "image_files" in request.FILES or image_urls:
            return redirect("product_detail", store_id=store_id, product_id=product.id)
        else:
            # Handle single image upload (legacy support)
            form = ImageUploadForm(request.POST, request.FILES)
            if form.is_valid():
                image = StoreImage.objects(store_id).create(
                    product=product,
                    name=form.cleaned_data["name"],
                    image_file=form.cleaned_data["image_file"],
                    image_code=form.cleaned_data.get("image_code", ""),
                )
                messages.success(
                    request, f'Image "{image.name}" uploaded successfully!'
                )
                return redirect(
                    "product_detail", store_id=store_id, product_id=product.id
                )
    else:
        form = ImageUploadForm()

    # Generate full URLs for images
    from django.utils.text import slugify

    image_data = []
    for image in images:
        image_url = request.build_absolute_uri(
            reverse(
                "image_view",
                kwargs={
                    "store_name": slugify(store.name),
                    "category_name": slugify(category.name),
                    "product_name": slugify(product.name),
                    "image_code": image.image_code,
                },
            )
        )
        image_data.append(
            {
                "id": image.id,
                "name": image.name,
                "image_code": image.image_code,
                "url": image_url,
            }
        )

    # Calculate discount percentage if both prices exist
    discount_percent = None
    if product.marked_price and product.min_discounted_price:
        try:
            discount = float(product.marked_price) - float(product.min_discounted_price)
            discount_percent = round((discount / float(product.marked_price)) * 100, 0)
        except (ValueError, ZeroDivisionError):
            discount_percent = None

    return render(
        request,
        "images/product_detail.html",
        {
            "product": product,
            "category": category,
            "store": store,
            "images": images,
            "image_data": image_data,
            "form": form,
            "discount_percent": discount_percent,
        },
    )


@login_required
@require_http_methods(["POST"])
def image_update(request, store_id, image_id):
    """Update image name and code"""
    from .store_helpers import StoreImage

    store = get_object_or_404(Store, id=store_id, user=request.user)
    image = StoreImage.objects(store_id).get(id=image_id)
    product = image.product
    category = product.category

    data = json.loads(request.body)
    image.name = data.get("name", image.name).strip()
    new_code = data.get("image_code", image.image_code).strip()

    # Validate image_code format
    if new_code:
        import re

        # Clean the code: lowercase, underscores only
        new_code = new_code.lower()
        new_code = re.sub(r"[^a-z0-9_]", "", new_code)
        new_code = re.sub(r"_+", "_", new_code)
        new_code = new_code.strip("_")

        if not new_code:
            return JsonResponse(
                {"success": False, "message": "Image code cannot be empty"}, status=400
            )

        image.image_code = new_code

    try:
        image.save()
        from django.utils.text import slugify

        return JsonResponse(
            {
                "success": True,
                "message": "Image updated successfully",
                "image": {
                    "id": image.id,
                    "name": image.name,
                    "image_code": image.image_code,
                    "url": request.build_absolute_uri(
                        reverse(
                            "image_view",
                            kwargs={
                                "store_name": slugify(store.name),
                                "category_name": slugify(category.name),
                                "product_name": slugify(product.name),
                                "image_code": image.image_code,
                            },
                        )
                    ),
                },
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@login_required
def image_delete(request, store_id, image_id):
    """Delete an image"""
    from .store_helpers import StoreImage

    store = get_object_or_404(Store, id=store_id, user=request.user)
    image = StoreImage.objects(store_id).get(id=image_id)
    product_id = image.product_id
    image.delete()
    messages.success(request, "Image deleted successfully!")
    return redirect("product_detail", store_id=store_id, product_id=product_id)


@csrf_exempt
def api_search_product(request):
    """API endpoint to search for products by name and return image URLs with fuzzy search (store-scoped)"""
    from django.db import connection
    from django.utils.text import slugify
    from rapidfuzz import fuzz, process

    try:
        # Accept both GET and POST requests
        product_name = request.POST.get("product_name") or request.GET.get(
            "product_name"
        )
        store_id = request.POST.get("store_id") or request.GET.get("store_id")
        store_name = request.POST.get("store_name") or request.GET.get("store_name")

        if not product_name:
            return JsonResponse(
                {"error": "product_name parameter is required"}, status=400
            )

        # Get store - required for scoping search
        store = None
        if store_id:
            try:
                store = Store.objects.get(id=store_id)
            except Store.DoesNotExist:
                return JsonResponse(
                    {"error": f"Store with ID {store_id} not found"}, status=404
                )
        elif store_name:
            try:
                store = Store.objects.get(name__iexact=store_name)
            except Store.DoesNotExist:
                return JsonResponse(
                    {"error": f'Store "{store_name}" not found'}, status=404
                )
            except Store.MultipleObjectsReturned:
                return JsonResponse(
                    {
                        "error": f'Multiple stores found with name "{store_name}". Please use store_id instead.'
                    },
                    status=400,
                )
        else:
            return JsonResponse(
                {"error": "store_id or store_name parameter is required"}, status=400
            )

        # Check if store tables exist, create them if they don't
        table_name = f"store_{store.id}_categories"
        with connection.cursor() as cursor:
            # Use string formatting to avoid Django debug SQL logging issues
            sql = "SELECT name FROM sqlite_master WHERE type='table' AND name = '{}'".format(
                table_name
            )
            cursor.execute(sql)
            if not cursor.fetchone():
                # Tables don't exist, create them
                from .store_tables import create_store_tables

                try:
                    create_store_tables(store.id)
                except Exception as e:
                    return JsonResponse(
                        {
                            "error": f"Store tables not initialized. Please contact administrator. Error: {str(e)}"
                        },
                        status=500,
                    )

        # Import store-specific helpers
        from .store_helpers import StoreCategory, StoreImage, StoreProduct

        # Filter products by store first
        # First try exact/partial match (case-insensitive) within the store
        try:
            products = StoreProduct.objects(store.id).filter(
                name__icontains=product_name
            )
        except Exception as e:
            return JsonResponse(
                {"error": f"Error querying products: {str(e)}"}, status=500
            )

        used_fuzzy = False

        # If no exact matches, try fuzzy search within the store
        if not products:
            used_fuzzy = True
            # Get all products in this store for fuzzy matching
            all_products = StoreProduct.objects(store.id).all()

            if all_products:
                # Create a list of product names with their IDs
                product_list = [(p.id, p.name) for p in all_products]

                # Use rapidfuzz to find best matches (score >= 60 for fuzzy matching)
                # Extract top 10 matches
                matches = process.extract(
                    product_name,
                    [p[1] for p in product_list],
                    limit=10,
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=60,  # Minimum similarity score (0-100)
                )

                if matches:
                    # Get product IDs from matches
                    matched_names = [match[0] for match in matches]
                    product_ids = [p[0] for p in product_list if p[1] in matched_names]
                    products = [p for p in all_products if p.id in product_ids]
                else:
                    # No fuzzy matches found
                    return JsonResponse(
                        {
                            "success": False,
                            "message": f'No products found matching "{product_name}" in store "{store.name}" (fuzzy search threshold: 60%)',
                            "results": [],
                        }
                    )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "message": f'No products found matching "{product_name}" in store "{store.name}"',
                        "results": [],
                    }
                )

        # Calculate similarity scores for ranking
        product_scores = []
        for product in products:
            # Calculate similarity score
            score = fuzz.token_sort_ratio(product_name.lower(), product.name.lower())
            product_scores.append((product, score))

        # Sort by score (highest first)
        product_scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for product, similarity_score in product_scores:
            try:
                category = product.category
                images = StoreImage.objects(store.id).filter(product_id=product.id)
                images_data = []
                for image in images:
                    image_url = request.build_absolute_uri(
                        reverse(
                            "image_view",
                            kwargs={
                                "store_name": slugify(store.name),
                                "category_name": slugify(category.name if category else "uncategorized"),
                                "product_name": slugify(product.name),
                                "image_code": image.image_code,
                            },
                        )
                    )
                    images_data.append(
                        {
                            "image_label": image.name,
                            "image_code": image.image_code,
                            "image_url": image_url,
                        }
                    )

                result = {
                    "store_name": store.name,
                    "category_name": category.name if category else "Uncategorized",
                    "product_name": product.name,
                    "images": images_data,
                    "image_count": len(images_data),
                    "similarity_score": similarity_score,
                }

                # Add price information if available
                if product.marked_price is not None:
                    result["marked_price"] = float(product.marked_price)
                if product.min_discounted_price is not None:
                    result["min_discounted_price"] = float(product.min_discounted_price)

                # Calculate discount percentage if both prices exist
                if product.marked_price and product.min_discounted_price:
                    try:
                        discount = float(product.marked_price) - float(
                            product.min_discounted_price
                        )
                        discount_percent = round(
                            (discount / float(product.marked_price)) * 100, 0
                        )
                        result["discount_percent"] = discount_percent
                    except (ValueError, ZeroDivisionError):
                        pass

                # Add description if available
                if product.description:
                    result["description"] = product.description
                
                results.append(result)
            except Exception as e:
                # Skip products with errors, but log them
                continue

        return JsonResponse(
            {
                "success": True,
                "query": product_name,
                "store_id": store.id,
                "store_name": store.name,
                "count": len(results),
                "search_type": "fuzzy" if used_fuzzy else "exact",
                "results": results,
            }
        )
    except Exception as e:
        # Catch any unexpected errors and return JSON
        import traceback

        return JsonResponse(
            {
                "success": False,
                "error": f"An error occurred: {str(e)}",
                "details": str(traceback.format_exc()) if settings.DEBUG else None,
            },
            status=500,
        )


@login_required
def api_test_page(request):
    """Frontend test page for API"""
    stores = Store.objects.filter(user=request.user)
    return render(request, "images/api_test.html", {"stores": stores})


@csrf_exempt
@require_http_methods(["POST"])
def api_store_create(request):
    """API endpoint to create a new store"""
    try:
        data = request.POST # For form data
        if not data and request.body:
             try:
                # Try parsing JSON if form data is empty
                import json
                data = json.loads(request.body)
             except:
                pass
        
        name = data.get("name")
        if not name:
            return JsonResponse({"success": False, "message": "Store Name is required"}, status=400)
            
        # Get user (either authenticated or provide user_id/username for API key scenarios if implemented, 
        # but for now assume session or fail)
        if not request.user.is_authenticated:
            # For pure API testing without session, we might need a workaround or expect token.
            # Assuming session auth for now as per constraints, or basic auth.
            return JsonResponse({"success": False, "message": "Authentication required"}, status=401)
            
        # Create Store
        store = Store(
            user=request.user,
            name=name,
            store_type=data.get("store_type"),
            description=data.get("description"),
            whatsapp_number=data.get("whatsapp_number"),
            website=data.get("website"),
            google_maps_link=data.get("google_maps_link"),
            logo_url=data.get("logo_url"),
            payment_qr_url=data.get("payment_qr_url"),
            maps_photo_url=data.get("maps_photo_url")
        )
        
        # Handle File Uploads (priority over URLs)
        if "logo" in request.FILES:
            store.logo = request.FILES["logo"]
        if "payment_qr" in request.FILES:
            store.payment_qr = request.FILES["payment_qr"]
        if "maps_photo" in request.FILES:
            store.maps_photo = request.FILES["maps_photo"]
            
        store.save()
        
        # Initialize tables
        try:
            from .store_tables import create_store_tables
            create_store_tables(store.id)
        except Exception as e:
            # Log error but don't fail the request completely
            print(f"Failed to create tables: {e}")
            
        return JsonResponse({
            "success": True, 
            "message": "Store created successfully",
            "store": {
                "id": store.id,
                "name": store.name,
                "logo_url": store.get_logo,
                "created_at": store.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required
def download_sample_csv(request):
    """Download a sample CSV file for bulk upload"""
    import csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products_sample.csv"'
    
    writer = csv.writer(response)
    # Header
    writer.writerow(['Category', 'Name', 'Marked Price', 'Min Discounted Price', 'Description', 'Image URLs'])
    # Sample data
    writer.writerow(['Electronics', 'Smartphone X', '50000', '45000', 'Flagship phone with 128GB storage', 'https://example.com/phone1.jpg,https://example.com/phone2.jpg'])
    writer.writerow(['Clothing', 'Men\'s T-Shirt', '1500', '1200', 'Cotton t-shirt, size M', ''])
    
    return response


@login_required
def product_bulk_upload(request, store_id):
    """Bulk upload products via CSV"""
    from .forms import BulkUploadForm
    from .store_helpers import StoreCategory, StoreProduct
    import csv 
    import io

    store = get_object_or_404(Store, id=store_id, user=request.user)
    
    if request.method == "POST":
        form = BulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            # Check if file is CSV
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a CSV file.')
                return render(request, "images/bulk_upload.html", {"form": form, "store": store})
                
            try:
                # Read CSV
                decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
                reader = csv.DictReader(decoded_file)
                
                # Verify headers
                required_headers = ['Category', 'Name']
                if not reader.fieldnames or not all(h in reader.fieldnames for h in required_headers):
                    messages.error(request, f'Invalid CSV format. Required columns: {", ".join(required_headers)}')
                    return render(request, "images/bulk_upload.html", {"form": form, "store": store})
                    
                products_created = 0
                categories_created = 0
                
                # Process rows
                for row in reader:
                    category_name = row.get('Category', '').strip()
                    product_name = row.get('Name', '').strip()
                    
                    if not category_name or not product_name:
                        continue
                        
                    # Get or Create Category
                    store_categories = StoreCategory.objects(store_id).filter(name__icontains=category_name)
                    # Simple case-insensitive name check logic
                    category = None
                    for c in store_categories:
                        if c.name.lower() == category_name.lower():
                            category = c
                            break
                    
                    if not category:
                        category = StoreCategory.objects(store_id).create(name=category_name)
                        categories_created += 1
                        
                    # Create Product
                    marked_price = row.get('Marked Price')
                    min_discounted_price = row.get('Min Discounted Price')
                    
                    # Clean prices (handle empty strings)
                    marked_price = float(marked_price) if marked_price and marked_price.strip() else None
                    min_discounted_price = float(min_discounted_price) if min_discounted_price and min_discounted_price.strip() else None
                    
                    product = StoreProduct.objects(store_id).create(
                        category=category,
                        name=product_name,
                        marked_price=marked_price,
                        min_discounted_price=min_discounted_price,
                        description=row.get('Description', '').strip()
                    )
                    
                    # Handle Image URLs
                    image_urls_str = row.get('Image URLs', '').strip()
                    if image_urls_str:
                        # Split by comma or semicolon
                        import re
                        urls = re.split(r'[;,]', image_urls_str)
                        for i, url in enumerate(urls):
                            url = url.strip()
                            if url:
                                try:
                                    # Create StoreImage
                                    # Generate a code if possible, or let auto-generation handle it
                                    from urllib.parse import urlparse
                                    import os
                                    
                                    path = urlparse(url).path
                                    filename = os.path.basename(path) or f"{product_name}_{i+1}"
                                    
                                    from .store_helpers import StoreImage
                                    StoreImage.objects(store_id).create(
                                        product=product,
                                        name=filename,
                                        url=url
                                    )
                                except Exception as img_err:
                                    print(f"Error adding image {url} for {product_name}: {img_err}")
                                    
                    products_created += 1
                    
                messages.success(request, f"Successfully uploaded {products_created} products (New categories: {categories_created})!")
                return redirect('store_detail', store_id=store.id)
                
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                messages.error(request, f'Error processing file: {str(e)}')
    else:
        form = BulkUploadForm()
        
    return render(request, "images/bulk_upload.html", {"form": form, "store": store})


def image_view(request, store_name, category_name, product_name, image_code):
    """Public view for accessing images by code"""
    import mimetypes

    from django.http import FileResponse, Http404
    from django.utils.text import slugify

    from .store_helpers import StoreCategory, StoreImage, StoreProduct

    # Find store by name (slugified)
    store = Store.objects.filter(name__iexact=store_name.replace("-", " ")).first()
    if not store:
        # Try exact match
        store = Store.objects.filter(name=store_name.replace("-", " ")).first()
    if not store:
        raise Http404("Store not found")

    # Find image by code in store-specific table
    images = StoreImage.objects(store.id).filter(image_code=image_code)
    if not images:
        raise Http404("Image not found")
    image = images[0]

    product = image.product
    category = product.category

    # Verify the URL path matches the image's store/category/product (case-insensitive, slugified comparison)
    if (
        slugify(store.name) != slugify(store_name)
        or slugify(category.name) != slugify(category_name)
        or slugify(product.name) != slugify(product_name)
    ):
        raise Http404("Image not found")

    # If image has a remote URL and no local file (or we prefer remote), redirect
    if getattr(image, 'url', None):
        from django.shortcuts import redirect
        return redirect(image.url)

    # Get file path and serve it
    from django.core.files.storage import default_storage

    file_path = image.image_file
    if file_path and default_storage.exists(file_path):
        file = default_storage.open(file_path, "rb")
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = "image/jpeg"
        return FileResponse(file, content_type=content_type)
    else:
        raise Http404("Image file not found")
