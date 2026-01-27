"""
Helper classes to provide Django ORM-like interface for store-specific tables
"""

import os

from django.core.files.uploadedfile import UploadedFile
from django.db import connection
from django.utils import timezone


class StoreCategory:
    """Category model for store-specific tables"""

    def __init__(self, store_id, data=None):
        self.store_id = store_id
        self.table_name = f"store_{store_id}_categories"
        if data:
            self.id = data.get("id")
            self.name = data.get("name")
            self.created_at = data.get("created_at")
            self.updated_at = data.get("updated_at")
        else:
            self.id = None
            self.name = None
            self.created_at = None
            self.updated_at = None

    def save(self):
        now = timezone.now()
        with connection.cursor() as cursor:
            if self.id:
                # Update
                sql = "UPDATE {} SET name = ?, updated_at = ? WHERE id = ?".format(
                    self.table_name
                )

                cursor.execute(sql, [self.name, now, self.id])
            else:
                # Create
                sql = "INSERT INTO {} (name, created_at, updated_at) VALUES (?, ?, ?)".format(
                    self.table_name
                )
                cursor.execute(sql, [self.name, now, now])
                self.id = cursor.lastrowid
                self.created_at = now
            self.updated_at = now

    def delete(self):
        if self.id:
            with connection.cursor() as cursor:
                sql = "DELETE FROM {} WHERE id = ?".format(self.table_name)
                cursor.execute(sql, [self.id])

    def __str__(self):
        return self.name or ""

    @classmethod
    def objects(cls, store_id):
        """Return a manager-like object"""
        return StoreCategoryManager(store_id)


class StoreCategoryManager:
    def __init__(self, store_id):
        self.store_id = store_id
        self.table_name = f"store_{store_id}_categories"

    def all(self):
        with connection.cursor() as cursor:
            sql = "SELECT * FROM {} ORDER BY name".format(self.table_name)
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            return [
                StoreCategory(self.store_id, dict(zip(columns, row)))
                for row in cursor.fetchall()
            ]

    def get(self, **kwargs):
        with connection.cursor() as cursor:
            conditions = []
            params = []
            for key, value in kwargs.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            where_clause = " AND ".join(conditions)
            sql = "SELECT * FROM {} WHERE {}".format(self.table_name, where_clause)
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if row:
                return StoreCategory(self.store_id, dict(zip(columns, row)))
            from django.core.exceptions import ObjectDoesNotExist

            raise ObjectDoesNotExist(f"Category matching query does not exist")

    def filter(self, **kwargs):
        with connection.cursor() as cursor:
            conditions = []
            params = []
            for key, value in kwargs.items():
                if "__" in key:
                    field, lookup = key.split("__", 1)
                    if lookup == "icontains":
                        conditions.append(f"{field} LIKE ?")
                        params.append(f"%{value}%")
                    else:
                        conditions.append(f"{field} = ?")
                        params.append(value)
                else:
                    conditions.append(f"{key} = ?")
                    params.append(value)
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            sql = "SELECT * FROM {} WHERE {} ORDER BY name".format(
                self.table_name, where_clause
            )
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            return [
                StoreCategory(self.store_id, dict(zip(columns, row)))
                for row in cursor.fetchall()
            ]

    def create(self, **kwargs):
        category = StoreCategory(self.store_id)
        for key, value in kwargs.items():
            setattr(category, key, value)
        category.save()
        return category


class StoreProduct:
    """Product model for store-specific tables"""

    def __init__(self, store_id, data=None):
        self.store_id = store_id
        self.table_name = f"store_{store_id}_products"
        if data:
            self.id = data.get("id")
            self.category_id = data.get("category_id")
            self.name = data.get("name")
            self.marked_price = data.get("marked_price")
            self.min_discounted_price = data.get("min_discounted_price")
            self.description = data.get("description")
            self.created_at = data.get("created_at")
            self.updated_at = data.get("updated_at")
            self._category = None
        else:
            self.id = None
            self.category_id = None
            self.name = None
            self.marked_price = None
            self.min_discounted_price = None
            self.description = None
            self.created_at = None
            self.updated_at = None
            self._category = None

    @property
    def category(self):
        if not self._category and self.category_id:
            try:
                self._category = StoreCategory.objects(self.store_id).get(
                    id=self.category_id
                )
            except:
                self._category = None
        return self._category

    @property
    def images(self):
        """Return images for this product"""
        return StoreImage.objects(self.store_id).filter(product_id=self.id)

    @category.setter
    def category(self, value):
        if isinstance(value, StoreCategory):
            self.category_id = value.id
            self._category = value
        else:
            self.category_id = value

    def save(self):
        now = timezone.now()
        with connection.cursor() as cursor:
            if self.id:
                # Update
                sql = "UPDATE {} SET category_id = ?, name = ?, marked_price = ?, min_discounted_price = ?, description = ?, updated_at = ? WHERE id = ?".format(
                    self.table_name
                )
                cursor.execute(
                    sql,
                    [
                        self.category_id,
                        self.name,
                        self.marked_price,
                        self.min_discounted_price,
                        self.description,
                        now,
                        self.id,
                    ],
                )
            else:
                # Create
                sql = "INSERT INTO {} (category_id, name, marked_price, min_discounted_price, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)".format(
                    self.table_name
                )
                cursor.execute(
                    sql,
                    [
                        self.category_id,
                        self.name,
                        self.marked_price,
                        self.min_discounted_price,
                        self.description,
                        now,
                        now,
                    ],
                )
                self.id = cursor.lastrowid
                self.created_at = now
            self.updated_at = now

    def delete(self):
        if self.id:
            with connection.cursor() as cursor:
                sql = "DELETE FROM {} WHERE id = ?".format(self.table_name)
                cursor.execute(sql, [self.id])

    def __str__(self):
        return self.name or ""

    @classmethod
    def objects(cls, store_id):
        return StoreProductManager(store_id)


class StoreProductManager:
    def __init__(self, store_id):
        self.store_id = store_id
        self.table_name = f"store_{store_id}_products"

    def all(self):
        with connection.cursor() as cursor:
            sql = "SELECT * FROM {} ORDER BY name".format(self.table_name)
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            return [
                StoreProduct(self.store_id, dict(zip(columns, row)))
                for row in cursor.fetchall()
            ]

    def get(self, **kwargs):
        with connection.cursor() as cursor:
            conditions = []
            params = []
            for key, value in kwargs.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            where_clause = " AND ".join(conditions)
            sql = "SELECT * FROM {} WHERE {}".format(self.table_name, where_clause)
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if row:
                return StoreProduct(self.store_id, dict(zip(columns, row)))
            from django.core.exceptions import ObjectDoesNotExist

            raise ObjectDoesNotExist(f"Product matching query does not exist")

    def filter(self, **kwargs):
        with connection.cursor() as cursor:
            conditions = []
            params = []
            for key, value in kwargs.items():
                if "__" in key:
                    field, lookup = key.split("__", 1)
                    if lookup == "icontains":
                        conditions.append(f"{field} LIKE ?")
                        params.append(f"%{value}%")
                    elif lookup == "in":
                        placeholders = ", ".join(["?" for _ in value])
                        conditions.append(f"{field} IN ({placeholders})")
                        params.extend(value)
                    else:
                        conditions.append(f"{field} = ?")
                        params.append(value)
                else:
                    conditions.append(f"{key} = ?")
                    params.append(value)
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            sql = "SELECT * FROM {} WHERE {} ORDER BY name".format(
                self.table_name, where_clause
            )
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            return [
                StoreProduct(self.store_id, dict(zip(columns, row)))
                for row in cursor.fetchall()
            ]

    def create(self, **kwargs):
        product = StoreProduct(self.store_id)
        for key, value in kwargs.items():
            if key == "category" and isinstance(value, StoreCategory):
                product.category_id = value.id
                product._category = value
            else:
                setattr(product, key, value)
        product.save()
        return product


class StoreImage:
    """Image model for store-specific tables"""

    def __init__(self, store_id, data=None):
        self.store_id = store_id
        self.table_name = f"store_{store_id}_images"
        if data:
            self.id = data.get("id")
            self.product_id = data.get("product_id")
            self.name = data.get("name")
            self.image_code = data.get("image_code")
            self.image_file = data.get("image_file")
            self.url = data.get("url")
            self.created_at = data.get("created_at")
            self.updated_at = data.get("updated_at")
            self._product = None
        else:
            self.id = None
            self.product_id = None
            self.name = None
            self.image_code = None
            self.image_file = None
            self.url = None
            self.created_at = None
            self.updated_at = None
            self._product = None

    @property
    def product(self):
        if not self._product and self.product_id:
            try:
                self._product = StoreProduct.objects(self.store_id).get(
                    id=self.product_id
                )
            except:
                self._product = None
        return self._product

    @product.setter
    def product(self, value):
        if isinstance(value, StoreProduct):
            self.product_id = value.id
            self._product = value
        else:
            self.product_id = value

    def save(self):
        import re
        from io import BytesIO

        from django.core.files.base import ContentFile
        from PIL import Image

        from .models import Store, generate_image_code, compress_image

        # Auto-generate image_code if not provided
        if not self.image_code or self.image_code.strip() == "":
            if self.image_file:
                if isinstance(self.image_file, UploadedFile):
                    self.image_code = generate_image_code(self.image_file.name)
                else:
                    self.image_code = generate_image_code(str(self.image_file))
            elif self.url:
                 # Try to get filename from URL
                 import os
                 from urllib.parse import urlparse
                 path = urlparse(self.url).path
                 filename = os.path.basename(path)
                 if filename:
                     self.image_code = generate_image_code(filename)
                 else:
                     self.image_code = generate_image_code(self.name)
            else:
                self.image_code = generate_image_code(self.name)
        else:
            # Clean the provided image_code
            self.image_code = self.image_code.strip().lower()
            self.image_code = re.sub(r"\s+", "_", self.image_code)
            self.image_code = re.sub(r"[^a-z0-9_]", "", self.image_code)
            self.image_code = re.sub(r"_+", "_", self.image_code)
            self.image_code = self.image_code.strip("_")

        # Ensure uniqueness within this store's table
        original_code = self.image_code
        counter = 1
        while True:
            existing_images = StoreImage.objects(self.store_id).filter(
                image_code=self.image_code
            )
            if not existing_images:
                break
            # Check if it's a same record update
            if self.id and existing_images[0].id == self.id:
                break
            self.image_code = f"{original_code}_{counter}"
            counter += 1

        # Apply logo watermark if it's a new upload
        if isinstance(self.image_file, UploadedFile):
            try:
                store = Store.objects.get(id=self.store_id)
                if store.logo:
                    # Open the uploaded image
                    self.image_file.seek(0)
                    image = Image.open(self.image_file)

                    # Open the logo
                    logo = Image.open(store.logo)

                    # Resize logo: 15% of image width
                    target_width = int(image.width * 0.15)
                    # Do not upscale logo
                    target_width = (
                        min(target_width, logo.width)
                        if logo.width > target_width
                        else logo.width
                    )

                    if target_width > 0:
                        aspect_ratio = logo.height / logo.width
                        target_height = int(target_width * aspect_ratio)
                        logo = logo.resize(
                            (target_width, target_height), Image.Resampling.LANCZOS
                        )

                        # Prepare for pasting (handle alpha channels)
                        if image.mode != "RGBA":
                            image = image.convert("RGBA")
                        if logo.mode != "RGBA":
                            logo = logo.convert("RGBA")

                        # Paste in top left (0, 0)
                        image.paste(logo, (0, 0), logo)

                        # Save back
                        output = BytesIO()
                        # Default to PNG for transparency support, but try to respect original format if possible
                        save_format = "PNG"
                        filename = self.image_file.name
                        ext = os.path.splitext(filename)[1].lower()

                        if ext in [".jpg", ".jpeg"]:
                            image = image.convert("RGB")
                            save_format = "JPEG"
                            # Use compression settings
                            image.save(output, format=save_format, quality=90, optimize=True)
                        elif ext == ".gif":
                            save_format = "GIF"
                            image.save(output, format=save_format)
                        else:
                            # PNG or others
                            image.save(output, format=save_format)
                            
                        # If PNG, we might want to optimize too, but quality param is different. 
                        # For now, focus on JPEG compression as requested.

                        output.seek(0)

                        # Replace the file content
                        self.image_file = ContentFile(output.read(), name=filename)
            except Exception as e:
                # Proceed without watermark on error, but ensure compression
                print(f"Error applying watermark: {str(e)}")
                if self.image_file and not self.url:
                     # Attempt generic compression
                     try:
                         # compress_image expects an object with .file, .name. 
                         # self.image_file is UploadedFile/ContentFile.
                         # We can try to wrap it effectively or just use it if it mimics FieldFile.
                         # Actually compress_image modifies .file attribute of the passed object.
                         # StoreImage.image_file IS the file object (UploadedFile). 
                         # So passing self directly won't work, passing self.image_file might not work if it doesn't have .file 
                         # (UploadedFile has .file, ContentFile might not in same way).
                         # Let's simplify: only compress if it's an UploadedFile (fresh upload).
                         if isinstance(self.image_file, UploadedFile):
                              # We need a wrapper to satisfy compress_image which updates field.file
                              # Or better, just replicate logic or make compress_image more flexible.
                              # Given I can't easily change compress_image signature everywhere if used by other models,
                              # I'll just replicate the basic safe logic or assume it works on the file wrapper.
                              # Actually, let's just use the Pillow logic directly here to be safe and explicit.
                              pass 
                     except:
                         pass

        # If we didn't apply watermark (or failed), we simply save the file. 
        # But we MUST compress it if it is a new upload.
        # Check if it is a new upload (UploadedFile matches) AND we haven't already processed it (ContentFile matches processed).
        # Note: In the watermark block above, we replaced self.image_file with ContentFile.
        # So if it is STILL UploadedFile, it means no watermark was applied.
        if isinstance(self.image_file, UploadedFile):
             try:
                 # Compress the raw upload
                 img = Image.open(self.image_file)
                 if img.mode != "RGB":
                     img = img.convert("RGB")
                 
                 output = BytesIO()
                 # Enforce 90% quality
                 img.save(output, format="JPEG", quality=90, optimize=True)
                 output.seek(0)
                 
                 # Create new ContentFile with .jpg extension
                 new_name = os.path.splitext(self.image_file.name)[0] + ".jpg"
                 self.image_file = ContentFile(output.read(), name=new_name)
             except Exception as e:
                 print(f"Compression failed: {e}")

        # Handle file upload saving
        file_path = None
        if isinstance(self.image_file, UploadedFile) or isinstance(
            self.image_file, ContentFile
        ):
            from django.core.files.storage import default_storage

            # self.image_file might be ContentFile now, ensure it has a name
            name = getattr(self.image_file, "name", "unnamed.jpg")
            file_path = default_storage.save(
                f"images/store_{self.store_id}/{name}", self.image_file
            )

        now = timezone.now()
        with connection.cursor() as cursor:
            if self.id:
                # Update
                if file_path:
                    sql = "UPDATE {} SET product_id = ?, name = ?, image_code = ?, image_file = ?, url = ?, updated_at = ? WHERE id = ?".format(
                        self.table_name
                    )
                    cursor.execute(
                        sql,
                        [
                            self.product_id,
                            self.name,
                            self.image_code,
                            file_path,
                            self.url,
                            now,
                            self.id,
                        ],
                    )
                else:
                    sql = "UPDATE {} SET product_id = ?, name = ?, image_code = ?, url = ?, updated_at = ? WHERE id = ?".format(
                        self.table_name
                    )
                    cursor.execute(
                        sql, [self.product_id, self.name, self.image_code, self.url, now, self.id]
                    )
            else:
                # Create
                if not file_path:
                    file_path = (
                        self.image_file if isinstance(self.image_file, str) else None
                    )
                sql = "INSERT INTO {} (product_id, name, image_code, image_file, url, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)".format(
                    self.table_name
                )
                cursor.execute(
                    sql,
                    [self.product_id, self.name, self.image_code, file_path, self.url, now, now],
                )
                self.id = cursor.lastrowid
                self.created_at = now
            self.updated_at = now

    def delete(self):
        if self.id:
            # Delete file if exists
            if self.image_file:
                from django.core.files.storage import default_storage

                try:
                    default_storage.delete(self.image_file)
                except:
                    pass
            with connection.cursor() as cursor:
                sql = "DELETE FROM {} WHERE id = ?".format(self.table_name)
                cursor.execute(sql, [self.id])

    def __str__(self):
        return f"{self.name} ({self.image_code})"

    @classmethod
    def objects(cls, store_id):
        return StoreImageManager(store_id)

    def get_absolute_url(self):
        """Return publicly accessible URL for the image"""
        from django.urls import reverse
        from django.utils.text import slugify

        from .models import Store

        store = Store.objects.get(id=self.store_id)
        product = self.product
        category = product.category
        return reverse(
            "image_view",
            kwargs={
                "store_name": slugify(store.name),
                "category_name": slugify(category.name),
                "product_name": slugify(product.name),
                "image_code": self.image_code,
            },
        )


class StoreImageManager:
    def __init__(self, store_id):
        self.store_id = store_id
        self.table_name = f"store_{store_id}_images"

    def all(self):
        with connection.cursor() as cursor:
            sql = "SELECT * FROM {} ORDER BY created_at DESC".format(self.table_name)
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            return [
                StoreImage(self.store_id, dict(zip(columns, row)))
                for row in cursor.fetchall()
            ]

    def get(self, **kwargs):
        with connection.cursor() as cursor:
            conditions = []
            params = []
            for key, value in kwargs.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            where_clause = " AND ".join(conditions)
            sql = "SELECT * FROM {} WHERE {}".format(self.table_name, where_clause)
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if row:
                return StoreImage(self.store_id, dict(zip(columns, row)))
            from django.core.exceptions import ObjectDoesNotExist

            raise ObjectDoesNotExist(f"Image matching query does not exist")

    def filter(self, **kwargs):
        with connection.cursor() as cursor:
            conditions = []
            params = []
            exclude_id = None
            for key, value in kwargs.items():
                if key == "exclude":
                    # Handle exclude separately
                    continue
                if "__" in key:
                    field, lookup = key.split("__", 1)
                    if lookup == "icontains":
                        conditions.append(f"{field} LIKE ?")
                        params.append(f"%{value}%")
                    else:
                        conditions.append(f"{field} = ?")
                        params.append(value)
                else:
                    conditions.append(f"{key} = ?")
                    params.append(value)

            # Handle exclude
            if "exclude" in kwargs:
                exclude_dict = kwargs["exclude"]
                if "id" in exclude_dict:
                    exclude_id = exclude_dict["id"]

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            if exclude_id:
                where_clause += f" AND id != {exclude_id}"

            sql = "SELECT * FROM {} WHERE {} ORDER BY created_at DESC".format(
                self.table_name, where_clause
            )
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            return [
                StoreImage(self.store_id, dict(zip(columns, row)))
                for row in cursor.fetchall()
            ]

    def exclude(self, **kwargs):
        """Exclude records matching the criteria"""
        with connection.cursor() as cursor:
            conditions = []
            params = []
            for key, value in kwargs.items():
                conditions.append(f"{key} != ?")
                params.append(value)
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            sql = "SELECT * FROM {} WHERE {} ORDER BY created_at DESC".format(
                self.table_name, where_clause
            )
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            return [
                StoreImage(self.store_id, dict(zip(columns, row)))
                for row in cursor.fetchall()
            ]

    def create(self, **kwargs):
        image = StoreImage(self.store_id)
        for key, value in kwargs.items():
            if key == "product" and isinstance(value, StoreProduct):
                image.product_id = value.id
                image._product = value
            else:
                setattr(image, key, value)
        image.save()
        return image

    def exists(self, **kwargs):
        with connection.cursor() as cursor:
            conditions = []
            params = []
            for key, value in kwargs.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            where_clause = " AND ".join(conditions)
            sql = "SELECT COUNT(*) FROM {} WHERE {}".format(
                self.table_name, where_clause
            )
            cursor.execute(sql, params)
            return cursor.fetchone()[0] > 0
