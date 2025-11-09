from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .models import Store, Category, Product, Image
from .forms import StoreForm, CategoryForm, ProductForm, ImageUploadForm
import json
import os
import re


def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Account created for {username}!')
                return redirect('store_list')
    else:
        form = UserCreationForm()
    return render(request, 'images/register.html', {'form': form})


def login_view(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('store_list')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'images/login.html')


@login_required
def store_list(request):
    """List all stores for the current user"""
    stores = Store.objects.filter(user=request.user)
    return render(request, 'images/store_list.html', {'stores': stores})


@login_required
def store_create(request):
    """Create a new store"""
    if request.method == 'POST':
        form = StoreForm(request.POST)
        if form.is_valid():
            store = form.save(commit=False)
            store.user = request.user
            store.save()
            messages.success(request, f'Store "{store.name}" created successfully!')
            return redirect('store_detail', store_id=store.id)
    else:
        form = StoreForm()
    return render(request, 'images/store_form.html', {'form': form, 'action': 'Create'})


@login_required
def store_detail(request, store_id):
    """View store details with categories and all images"""
    from django.utils.text import slugify
    
    store = get_object_or_404(Store, id=store_id, user=request.user)
    categories = store.categories.all()
    
    # Collect all images organized by category and product
    images_by_category = []
    for category in categories:
        products_data = []
        for product in category.products.all():
            images_data = []
            for image in product.images.all():
                image_url = request.build_absolute_uri(reverse('image_view', kwargs={
                    'store_name': slugify(store.name),
                    'category_name': slugify(category.name),
                    'product_name': slugify(product.name),
                    'image_code': image.image_code
                }))
                images_data.append({
                    'id': image.id,
                    'name': image.name,
                    'image_code': image.image_code,
                    'url': image_url,
                })
            if images_data:
                products_data.append({
                    'product': product,
                    'images': images_data,
                })
        if products_data:
            images_by_category.append({
                'category': category,
                'products': products_data,
            })
    
    return render(request, 'images/store_detail.html', {
        'store': store,
        'categories': categories,
        'images_by_category': images_by_category,
    })


@login_required
def category_create(request, store_id):
    """Create a new category"""
    store = get_object_or_404(Store, id=store_id, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.store = store
            category.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('store_detail', store_id=store.id)
    else:
        form = CategoryForm()
    return render(request, 'images/category_form.html', {
        'form': form,
        'store': store,
        'action': 'Create'
    })


@login_required
def category_detail(request, category_id):
    """View category details with products"""
    category = get_object_or_404(Category, id=category_id, store__user=request.user)
    products = category.products.all()
    return render(request, 'images/category_detail.html', {
        'category': category,
        'store': category.store,
        'products': products,
    })


@login_required
def product_create(request, category_id):
    """Create a new product"""
    category = get_object_or_404(Category, id=category_id, store__user=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.category = category
            product.save()
            messages.success(request, f'Product "{product.name}" created successfully!')
            return redirect('product_detail', product_id=product.id)
    else:
        form = ProductForm()
    return render(request, 'images/product_form.html', {
        'form': form,
        'category': category,
        'action': 'Create'
    })


@login_required
def product_detail(request, product_id):
    """View product details and upload images"""
    product = get_object_or_404(Product, id=product_id, category__store__user=request.user)
    images = product.images.all()
    
    if request.method == 'POST':
        # Check if it's a multiple upload
        if 'image_files' in request.FILES:
            # Handle multiple image uploads
            files = request.FILES.getlist('image_files')
            labels = request.POST.getlist('image_labels', [])
            image_codes = request.POST.getlist('image_codes', [])
            
            uploaded_count = 0
            for idx, file in enumerate(files):
                # Get label for this image (use filename without extension if no label provided)
                if idx < len(labels) and labels[idx].strip():
                    label = labels[idx].strip()
                else:
                    # Use filename without extension as fallback
                    label = os.path.splitext(file.name)[0]
                
                # Get image code (use provided code or empty string for auto-generation)
                image_code = ''
                if idx < len(image_codes) and image_codes[idx].strip():
                    # Clean the provided image code
                    code = image_codes[idx].strip().lower()
                    code = re.sub(r'[^a-z0-9_]', '', code)
                    code = re.sub(r'_+', '_', code)
                    code = code.strip('_')
                    if code:
                        image_code = code
                
                # Create image instance
                image = Image(
                    product=product,
                    name=label,
                    image_file=file,
                    image_code=image_code  # Will be auto-generated if empty
                )
                image.save()
                uploaded_count += 1
            
            if uploaded_count > 0:
                messages.success(request, f'Successfully uploaded {uploaded_count} image(s)!')
            return redirect('product_detail', product_id=product.id)
        else:
            # Handle single image upload (legacy support)
            form = ImageUploadForm(request.POST, request.FILES)
            if form.is_valid():
                image = form.save(commit=False)
                image.product = product
                image.save()
                messages.success(request, f'Image "{image.name}" uploaded successfully!')
                return redirect('product_detail', product_id=product.id)
    else:
        form = ImageUploadForm()
    
    # Generate full URLs for images
    from django.utils.text import slugify
    image_data = []
    for image in images:
        image_url = request.build_absolute_uri(reverse('image_view', kwargs={
            'store_name': slugify(product.category.store.name),
            'category_name': slugify(product.category.name),
            'product_name': slugify(product.name),
            'image_code': image.image_code
        }))
        image_data.append({
            'id': image.id,
            'name': image.name,
            'image_code': image.image_code,
            'url': image_url,
        })
    
    return render(request, 'images/product_detail.html', {
        'product': product,
        'category': product.category,
        'store': product.category.store,
        'images': images,
        'image_data': image_data,
        'form': form,
    })


@login_required
@require_http_methods(["POST"])
def image_update(request, image_id):
    """Update image name and code"""
    image = get_object_or_404(Image, id=image_id, product__category__store__user=request.user)
    
    data = json.loads(request.body)
    image.name = data.get('name', image.name).strip()
    new_code = data.get('image_code', image.image_code).strip()
    
    # Validate image_code format
    if new_code:
        import re
        # Clean the code: lowercase, underscores only
        new_code = new_code.lower()
        new_code = re.sub(r'[^a-z0-9_]', '', new_code)
        new_code = re.sub(r'_+', '_', new_code)
        new_code = new_code.strip('_')
        
        if not new_code:
            return JsonResponse({'success': False, 'message': 'Image code cannot be empty'}, status=400)
        
        image.image_code = new_code
    
    try:
        image.save()
        from django.utils.text import slugify
        return JsonResponse({
            'success': True,
            'message': 'Image updated successfully',
            'image': {
                'id': image.id,
                'name': image.name,
                'image_code': image.image_code,
                'url': request.build_absolute_uri(reverse('image_view', kwargs={
                    'store_name': slugify(image.product.category.store.name),
                    'category_name': slugify(image.product.category.name),
                    'product_name': slugify(image.product.name),
                    'image_code': image.image_code
                })),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
def image_delete(request, image_id):
    """Delete an image"""
    image = get_object_or_404(Image, id=image_id, product__category__store__user=request.user)
    product_id = image.product.id
    image.delete()
    messages.success(request, 'Image deleted successfully!')
    return redirect('product_detail', product_id=product_id)


@csrf_exempt
def api_search_product(request):
    """API endpoint to search for products by name and return image URLs with fuzzy search"""
    from django.utils.text import slugify
    from rapidfuzz import fuzz, process
    
    # Accept both GET and POST requests
    product_name = request.POST.get('product_name') or request.GET.get('product_name')
    
    if not product_name:
        return JsonResponse({'error': 'product_name parameter is required'}, status=400)
    
    # First try exact/partial match (case-insensitive)
    products = Product.objects.filter(name__icontains=product_name)
    used_fuzzy = False
    
    # If no exact matches, try fuzzy search
    if not products.exists():
        used_fuzzy = True
        # Get all products for fuzzy matching
        all_products = Product.objects.all()
        
        if all_products.exists():
            # Create a list of product names with their IDs
            product_list = [(p.id, p.name) for p in all_products]
            
            # Use rapidfuzz to find best matches (score >= 60 for fuzzy matching)
            # Extract top 10 matches
            matches = process.extract(
                product_name,
                [p[1] for p in product_list],
                limit=10,
                scorer=fuzz.partial_ratio,
                score_cutoff=60  # Minimum similarity score (0-100)
            )
            
            if matches:
                # Get product IDs from matches
                matched_names = [match[0] for match in matches]
                product_ids = [p[0] for p in product_list if p[1] in matched_names]
                products = Product.objects.filter(id__in=product_ids)
            else:
                # No fuzzy matches found
                return JsonResponse({
                    'success': False,
                    'message': f'No products found matching "{product_name}" (fuzzy search threshold: 60%)',
                    'results': []
                })
        else:
            return JsonResponse({
                'success': False,
                'message': f'No products found matching "{product_name}"',
                'results': []
            })
    
    # Calculate similarity scores for ranking
    product_scores = []
    for product in products:
        # Calculate similarity score
        score = fuzz.partial_ratio(product_name.lower(), product.name.lower())
        product_scores.append((product, score))
    
    # Sort by score (highest first)
    product_scores.sort(key=lambda x: x[1], reverse=True)
    
    results = []
    for product, similarity_score in product_scores:
        images_data = []
        for image in product.images.all():
            image_url = request.build_absolute_uri(reverse('image_view', kwargs={
                'store_name': slugify(product.category.store.name),
                'category_name': slugify(product.category.name),
                'product_name': slugify(product.name),
                'image_code': image.image_code
            }))
            images_data.append({
                'image_label': image.name,
                'image_code': image.image_code,
                'image_url': image_url,
            })
        
        results.append({
            'store_name': product.category.store.name,
            'category_name': product.category.name,
            'product_name': product.name,
            'images': images_data,
            'image_count': len(images_data),
            'similarity_score': similarity_score  # Add similarity score to results
        })
    
    return JsonResponse({
        'success': True,
        'query': product_name,
        'count': len(results),
        'search_type': 'fuzzy' if used_fuzzy else 'exact',
        'results': results
    })


def api_test_page(request):
    """Frontend test page for API"""
    return render(request, 'images/api_test.html')


def image_view(request, store_name, category_name, product_name, image_code):
    """Public view for accessing images by code"""
    from django.http import FileResponse
    import mimetypes
    from django.utils.text import slugify
    
    # Find image by code first
    image = get_object_or_404(Image, image_code=image_code)
    
    # Verify the URL path matches the image's store/category/product (case-insensitive, slugified comparison)
    if (slugify(image.product.category.store.name) != slugify(store_name) or
        slugify(image.product.category.name) != slugify(category_name) or
        slugify(image.product.name) != slugify(product_name)):
        from django.http import Http404
        raise Http404("Image not found")
    
    content_type, _ = mimetypes.guess_type(image.image_file.name)
    if not content_type:
        content_type = 'image/jpeg'
    return FileResponse(image.image_file.open('rb'), content_type=content_type)

