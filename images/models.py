import os
import re
import sys
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from PIL import Image as PilImage


def compress_image(image_field, quality=90):
    """Compress the image field using Pillow"""
    if not image_field:
        return

    # Open image using Pillow
    img = PilImage.open(image_field)

    # Convert to RGB (in case of RGBA/P)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Compress
    output = BytesIO()
    img.save(output, format="JPEG", quality=quality, optimize=True)
    output.seek(0)

    # Update the image field
    image_field.file = InMemoryUploadedFile(
        output,
        "ImageField",
        f"{os.path.splitext(image_field.name)[0]}.jpg",
        "image/jpeg",
        sys.getsizeof(output),
        None,
    )


def generate_image_code(filename):
    """Generate image code from filename: lowercase, words separated by underscores"""
    # Remove file extension
    name = os.path.splitext(filename)[0]
    # Replace spaces and special characters with underscores
    name = re.sub(r"[^a-zA-Z0-9\s]", "", name)
    # Replace multiple spaces with single space
    name = re.sub(r"\s+", " ", name)
    # Convert to lowercase and replace spaces with underscores
    code = name.lower().strip().replace(" ", "_")
    # Remove multiple underscores
    code = re.sub(r"_+", "_", code)
    return code


class Store(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stores")
    # Added logo field
    logo = models.ImageField(upload_to="store_logos/", blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True, help_text="Public URL for logo (if not uploaded)")

    # New fields
    payment_qr = models.ImageField(upload_to="payment_qrs/", blank=True, null=True, help_text="Upload your Payment QR Code")
    payment_qr_url = models.URLField(blank=True, null=True, help_text="Public URL for Payment QR")
    
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True, help_text="e.g., +9779812345678")
    website = models.URLField(blank=True, null=True)
    google_maps_link = models.URLField(blank=True, null=True)
    
    maps_photo = models.ImageField(upload_to="store_maps/", blank=True, null=True, help_text="Upload a photo of your store location/map")
    maps_photo_url = models.URLField(blank=True, null=True, help_text="Public URL for Map Photo")
    
    store_type = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Clothing, Electronics, Grocery")
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        
    @property
    def get_logo(self):
        if self.logo:
            return self.logo.url
        return self.logo_url
        
    @property
    def get_payment_qr(self):
        if self.payment_qr:
            return self.payment_qr.url
        return self.payment_qr_url
        
    @property
    def get_maps_photo(self):
        if self.maps_photo:
            return self.maps_photo.url
        return self.maps_photo_url

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Compress logo
        if self.logo and isinstance(self.logo.file, InMemoryUploadedFile):
            compress_image(self.logo)
            
        # Compress payment_qr
        if self.payment_qr and isinstance(self.payment_qr.file, InMemoryUploadedFile):
            compress_image(self.payment_qr)
            
        # Compress maps_photo
        if self.maps_photo and isinstance(self.maps_photo.file, InMemoryUploadedFile):
            compress_image(self.maps_photo)
            
        super().save(*args, **kwargs)


class Category(models.Model):
    store = models.ForeignKey(
        Store, on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return f"{self.store.name} - {self.name}"


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Image(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    name = models.CharField(max_length=200)
    image_code = models.CharField(max_length=200, unique=True)
    image_file = models.ImageField(upload_to="images/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.image_code})"

    def save(self, *args, **kwargs):
        # Compress image if it's a new upload
        if self.image_file and isinstance(self.image_file.file, InMemoryUploadedFile):
            compress_image(self.image_file)

        # Auto-generate image_code if not provided or empty
        if not self.image_code or self.image_code.strip() == "":
            if self.image_file:
                self.image_code = generate_image_code(self.image_file.name)
            else:
                self.image_code = generate_image_code(self.name)
        else:
            # Clean the provided image_code
            self.image_code = self.image_code.strip().lower()
            # Replace spaces with underscores
            self.image_code = re.sub(r"\s+", "_", self.image_code)
            # Remove invalid characters
            self.image_code = re.sub(r"[^a-z0-9_]", "", self.image_code)
            # Remove multiple underscores
            self.image_code = re.sub(r"_+", "_", self.image_code)
            self.image_code = self.image_code.strip("_")

        # Ensure uniqueness
        original_code = self.image_code
        counter = 1
        while (
            Image.objects.filter(image_code=self.image_code)
            .exclude(pk=self.pk)
            .exists()
        ):
            self.image_code = f"{original_code}_{counter}"
            counter += 1

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Return publicly accessible URL for the image"""
        from django.urls import reverse
        from django.utils.text import slugify

        return reverse(
            "image_view",
            kwargs={
                "store_name": slugify(self.product.category.store.name),
                "category_name": slugify(self.product.category.name),
                "product_name": slugify(self.product.name),
                "image_code": self.image_code,
            },
        )
