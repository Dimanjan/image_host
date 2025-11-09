from django.db import models
from django.contrib.auth.models import User
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


class Store(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stores')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Category(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return f"{self.store.name} - {self.name}"


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Image(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    name = models.CharField(max_length=200)
    image_code = models.CharField(max_length=200, unique=True)
    image_file = models.ImageField(upload_to='images/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.image_code})"

    def save(self, *args, **kwargs):
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
        
        # Ensure uniqueness
        original_code = self.image_code
        counter = 1
        while Image.objects.filter(image_code=self.image_code).exclude(pk=self.pk).exists():
            self.image_code = f"{original_code}_{counter}"
            counter += 1
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Return publicly accessible URL for the image"""
        from django.urls import reverse
        from django.utils.text import slugify
        return reverse('image_view', kwargs={
            'store_name': slugify(self.product.category.store.name),
            'category_name': slugify(self.product.category.name),
            'product_name': slugify(self.product.name),
            'image_code': self.image_code
        })

