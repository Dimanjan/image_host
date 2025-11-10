"""
Dynamic model system for store-specific tables.
Each store gets its own set of tables: store_{store_id}_categories, store_{store_id}_products, store_{store_id}_images
"""
from django.db import models
from django.contrib.auth.models import User
from django.apps import apps
import os
import re


def generate_image_code(filename):
    """Generate image code from filename: lowercase, words separated by underscores"""
    # Remove file extension
    name = os.path.splitext(filename)[0]
    # Replace spaces and special characters with underscores
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)
    # Convert to lowercase and replace spaces with underscores
    code = name.lower().strip().replace(' ', '_')
    # Remove multiple underscores
    code = re.sub(r'_+', '_', code)
    return code


def get_store_category_model(store_id):
    """Get the Category model for a specific store"""
    model_name = f'Store{store_id}Category'
    
    # Check if model already exists in app registry
    if model_name in apps.all_models.get('images', {}):
        return apps.get_model('images', model_name)
    
    # Create dynamic model
    class Meta:
        db_table = f'store_{store_id}_categories'
        ordering = ['name']
        verbose_name_plural = 'categories'
        app_label = 'images'
    
    attrs = {
        '__module__': 'images.store_models',
        'Meta': Meta,
        'id': models.BigAutoField(primary_key=True),
        'name': models.CharField(max_length=200),
        'created_at': models.DateTimeField(auto_now_add=True),
        'updated_at': models.DateTimeField(auto_now=True),
        '__str__': lambda self: f"Store {store_id} - {self.name}",
    }
    
    model = type(model_name, (models.Model,), attrs)
    apps.all_models['images'][model_name] = model
    return model


def get_store_product_model(store_id, category_model):
    """Get the Product model for a specific store"""
    model_name = f'Store{store_id}Product'
    
    # Check if model already exists in app registry
    if model_name in apps.all_models.get('images', {}):
        return apps.get_model('images', model_name)
    
    # Create dynamic model
    class Meta:
        db_table = f'store_{store_id}_products'
        ordering = ['name']
        app_label = 'images'
    
    attrs = {
        '__module__': 'images.store_models',
        'Meta': Meta,
        'id': models.BigAutoField(primary_key=True),
        'category': models.ForeignKey(category_model, on_delete=models.CASCADE, related_name='products'),
        'name': models.CharField(max_length=200),
        'created_at': models.DateTimeField(auto_now_add=True),
        'updated_at': models.DateTimeField(auto_now=True),
        '__str__': lambda self: f"{self.category.name} - {self.name}",
    }
    
    model = type(model_name, (models.Model,), attrs)
    apps.all_models['images'][model_name] = model
    return model


def get_store_image_model(store_id, product_model):
    """Get the Image model for a specific store"""
    model_name = f'Store{store_id}Image'
    
    # Check if model already exists in app registry
    if model_name in apps.all_models.get('images', {}):
        return apps.get_model('images', model_name)
    
    # Create dynamic model
    class Meta:
        db_table = f'store_{store_id}_images'
        ordering = ['-created_at']
        app_label = 'images'
    
    def save_image(self, *args, **kwargs):
        # Auto-generate image_code if not provided or empty
        if not self.image_code or self.image_code.strip() == '':
            if self.image_file:
                self.image_code = generate_image_code(self.image_file.name)
            else:
                self.image_code = generate_image_code(self.name)
        else:
            # Clean the provided image_code
            self.image_code = self.image_code.strip().lower()
            # Replace spaces with underscores
            self.image_code = re.sub(r'\s+', '_', self.image_code)
            # Remove invalid characters
            self.image_code = re.sub(r'[^a-z0-9_]', '', self.image_code)
            # Remove multiple underscores
            self.image_code = re.sub(r'_+', '_', self.image_code)
            self.image_code = self.image_code.strip('_')
        
        # Ensure uniqueness within this store's table
        original_code = self.image_code
        counter = 1
        # Get the model class for this store to check uniqueness
        ImageModel = get_store_image_model(store_id, product_model)
        while ImageModel.objects.filter(image_code=self.image_code).exclude(pk=self.pk).exists():
            self.image_code = f"{original_code}_{counter}"
            counter += 1
        
        super(ImageModel, self).save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Return publicly accessible URL for the image"""
        from django.urls import reverse
        from django.utils.text import slugify
        from .models import Store
        store = Store.objects.get(id=store_id)
        return reverse('image_view', kwargs={
            'store_name': slugify(store.name),
            'category_name': slugify(self.product.category.name),
            'product_name': slugify(self.product.name),
            'image_code': self.image_code
        })
    
    attrs = {
        '__module__': 'images.store_models',
        'Meta': Meta,
        'id': models.BigAutoField(primary_key=True),
        'product': models.ForeignKey(product_model, on_delete=models.CASCADE, related_name='images'),
        'name': models.CharField(max_length=200),
        'image_code': models.CharField(max_length=200),  # Not unique globally, but unique per store
        'image_file': models.ImageField(upload_to=f'images/store_{store_id}/'),
        'created_at': models.DateTimeField(auto_now_add=True),
        'updated_at': models.DateTimeField(auto_now=True),
        'save': save_image,
        'get_absolute_url': get_absolute_url,
        '__str__': lambda self: f"{self.name} ({self.image_code})",
    }
    
    model = type(model_name, (models.Model,), attrs)
    apps.all_models['images'][model_name] = model
    return model

