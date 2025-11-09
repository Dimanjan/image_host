from django.contrib import admin
from .models import Store, Category, Product, Image


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'user__username']


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

