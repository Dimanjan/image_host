from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Store, Category, Product, Image
from .store_models import get_store_category_model, get_store_product_model, get_store_image_model

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at', 'get_product_count', 'get_image_count']
    list_filter = ['created_at']
    search_fields = ['name', 'user__username']
    # Add the inventory display to the readonly fields so it appears on the detail page
    readonly_fields = ['store_inventory_display']

    def get_product_count(self, obj):
        """Display number of products in the store list view"""
        try:
            CategoryModel = get_store_category_model(obj.id)
            ProductModel = get_store_product_model(obj.id, CategoryModel)
            return ProductModel.objects.count()
        except Exception:
            return 0
    get_product_count.short_description = 'Products'

    def get_image_count(self, obj):
        """Display number of images in the store list view"""
        try:
            CategoryModel = get_store_category_model(obj.id)
            ProductModel = get_store_product_model(obj.id, CategoryModel)
            ImageModel = get_store_image_model(obj.id, ProductModel)
            return ImageModel.objects.count()
        except Exception:
            return 0
    get_image_count.short_description = 'Images'

    def store_inventory_display(self, obj):
        """Render a table of the store's products and images"""
        try:
            # Initialize dynamic models for this specific store
            CategoryModel = get_store_category_model(obj.id)
            ProductModel = get_store_product_model(obj.id, CategoryModel)
            ImageModel = get_store_image_model(obj.id, ProductModel)
            
            # Fetch products with their categories and images
            # Note: We can't use standard select_related for images as they are reverse FK, 
            # but we can prefetch or just access them if the model is initialized.
            products = ProductModel.objects.all().select_related('category')
            
            if not products.exists():
                return "No products found in this store."

            # Build HTML table
            html = """
            <div style="max-height: 600px; overflow-y: auto; border: 1px solid #eee;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead style="background-color: #f5f5f5; position: sticky; top: 0;">
                        <tr>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Product Name</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Category</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">Price</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">Discounted</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Images</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Description</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for p in products:
                # Calculate image count
                # The dynamic Image model relates to Product with related_name='images'
                image_count = p.images.count()
                
                html += f"""
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">{p.name}</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{p.category.name}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{p.marked_price or '-'}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{p.min_discounted_price or '-'}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{image_count}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; color: #666; font-size: 0.9em;">{(p.description or '')[:100]}</td>
                    </tr>
                """
            
            html += """
                    </tbody>
                </table>
            </div>
            """
            return mark_safe(html)
            
        except Exception as e:
            return f"Unable to load store data (Tables might not exist yet): {str(e)}"
    
    store_inventory_display.short_description = "Store Inventory (Dynamic Data)"


# We keep these registered to avoid errors, but they will likely be empty
# because the app uses dynamic store_{id}_* tables instead of these global tables.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'store', 'created_at']
    list_filter = ['store', 'created_at']
    search_fields = ['name', 'store__name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'category__name']

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['name', 'image_code', 'product', 'created_at']
    list_filter = ['product', 'created_at']
    search_fields = ['name', 'image_code']