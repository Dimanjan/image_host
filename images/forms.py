from django import forms

from .models import Category, Image, Product, Store


class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = [
            "name", 
            "logo", 
            "store_type", 
            "description", 
            "whatsapp_number", 
            "website", 
            "google_maps_link", 
            "maps_photo", 
            "payment_qr"
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter store name"}),
            "logo": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "store_type": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Clothing, Electronics"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Describe your store..."}),
            "whatsapp_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "9812345678"}),
            "website": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://example.com"}),
            "google_maps_link": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://maps.google.com/..."}),
            "maps_photo": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "payment_qr": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }

    def clean_whatsapp_number(self):
        number = self.cleaned_data.get("whatsapp_number")
        if number:
            # Strip spaces, hyphens, and brackets
            import re
            cleaned_number = re.sub(r"[^\d+]", "", number)
            
            # Basic validation
            if not re.match(r"^\+?\d{7,15}$", cleaned_number):
                raise forms.ValidationError("Please enter a valid phone number (7-15 digits), optionally with + prefix.")
            
            return cleaned_number
        return number


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter category name",
                    "required": True,
                }
            ),
        }


class ProductForm(forms.Form):
    """Form for creating/editing products with price fields"""

    name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter product name",
                "required": True,
            }
        ),
    )
    marked_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "0.00",
                "step": "0.01",
                "min": "0",
            }
        ),
    )
    min_discounted_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "0.00",
                "step": "0.01",
                "min": "0",
            }
        ),
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Enter product details, features, specifications, etc.",
                "rows": 5,
            }
        ),
    )


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ["name", "image_file", "image_code"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter image name",
                    "required": True,
                }
            ),
            "image_file": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                    "required": True,
                }
            ),
            "image_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Auto-generated from filename",
                }
            ),
        }


class BulkUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Select CSV File",
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": ".csv",
                "required": True
            }
        )
    )
