from django import forms
from .models import Store, Category, Product, Image


class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter store name',
                'required': True,
            }),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name',
                'required': True,
            }),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name',
                'required': True,
            }),
        }


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['name', 'image_file', 'image_code']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter image name',
                'required': True,
            }),
            'image_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'required': True,
            }),
            'image_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto-generated from filename',
            }),
        }



