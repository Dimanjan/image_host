"""
System to create and manage store-specific database tables.
Each store gets its own tables: store_{store_id}_categories, store_{store_id}_products, store_{store_id}_images
"""
from django.db import connection
from django.core.management import call_command
from django.apps import apps
import os


def create_store_tables(store_id):
    """
    Create database tables for a specific store.
    Creates: store_{store_id}_categories, store_{store_id}_products, store_{store_id}_images
    """
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Create categories table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS store_{store_id}_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)
        
        # Create products table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS store_{store_id}_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name VARCHAR(200) NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (category_id) REFERENCES store_{store_id}_categories(id) ON DELETE CASCADE
            )
        """)
        
        # Create images table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS store_{store_id}_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                name VARCHAR(200) NOT NULL,
                image_code VARCHAR(200) NOT NULL,
                image_file VARCHAR(100) NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (product_id) REFERENCES store_{store_id}_products(id) ON DELETE CASCADE
            )
        """)
        
        # Create unique index on image_code (SQLite doesn't support UNIQUE in CREATE TABLE the same way)
        cursor.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_store_{store_id}_images_code_unique ON store_{store_id}_images(image_code)")
        
        # Create indexes for better performance
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_store_{store_id}_categories_name ON store_{store_id}_categories(name)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_store_{store_id}_products_category ON store_{store_id}_products(category_id)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_store_{store_id}_products_name ON store_{store_id}_products(name)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_store_{store_id}_images_product ON store_{store_id}_images(product_id)")


def drop_store_tables(store_id):
    """Drop all tables for a specific store"""
    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS store_{store_id}_images")
        cursor.execute(f"DROP TABLE IF EXISTS store_{store_id}_products")
        cursor.execute(f"DROP TABLE IF EXISTS store_{store_id}_categories")


class StoreCategoryManager:
    """Manager for store-specific Category operations"""
    def __init__(self, store_id):
        self.store_id = store_id
        self.table_name = f'store_{store_id}_categories'
    
    def all(self):
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY name")
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get(self, **kwargs):
        with connection.cursor() as cursor:
            conditions = []
            params = []
            for key, value in kwargs.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            where_clause = " AND ".join(conditions)
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE {where_clause}", params)
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if row:
                return dict(zip(columns, row))
            return None
    
    def filter(self, **kwargs):
        with connection.cursor() as cursor:
            conditions = []
            params = []
            for key, value in kwargs.items():
                if '__' in key:
                    # Handle lookups like name__icontains
                    field, lookup = key.split('__', 1)
                    if lookup == 'icontains':
                        conditions.append(f"{field} LIKE ?")
                        params.append(f"%{value}%")
                    else:
                        conditions.append(f"{field} = ?")
                        params.append(value)
                else:
                    conditions.append(f"{key} = ?")
                    params.append(value)
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE {where_clause} ORDER BY name", params)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def create(self, **kwargs):
        with connection.cursor() as cursor:
            from django.utils import timezone
            now = timezone.now()
            fields = list(kwargs.keys()) + ['created_at', 'updated_at']
            values = list(kwargs.values()) + [now, now]
            placeholders = ', '.join(['?' for _ in values])
            field_names = ', '.join(fields)
            cursor.execute(
                f"INSERT INTO {self.table_name} ({field_names}) VALUES ({placeholders})",
                values
            )
            return cursor.lastrowid
    
    def delete(self, id):
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {self.table_name} WHERE id = ?", [id])


class StoreProductManager:
    """Manager for store-specific Product operations"""
    def __init__(self, store_id):
        self.store_id = store_id
        self.table_name = f'store_{store_id}_products'
    
    def all(self):
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY name")
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get(self, **kwargs):
        with connection.cursor() as cursor:
            conditions = []
            params = []
            for key, value in kwargs.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            where_clause = " AND ".join(conditions)
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE {where_clause}", params)
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if row:
                return dict(zip(columns, row))
            return None
    
    def filter(self, **kwargs):
        with connection.cursor() as cursor:
            conditions = []
            params = []
            for key, value in kwargs.items():
                if '__' in key:
                    field, lookup = key.split('__', 1)
                    if lookup == 'icontains':
                        conditions.append(f"{field} LIKE ?")
                        params.append(f"%{value}%")
                    elif lookup == 'in':
                        placeholders = ', '.join(['?' for _ in value])
                        conditions.append(f"{field} IN ({placeholders})")
                        params.extend(value)
                    else:
                        conditions.append(f"{field} = ?")
                        params.append(value)
                else:
                    conditions.append(f"{key} = ?")
                    params.append(value)
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE {where_clause} ORDER BY name", params)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def create(self, **kwargs):
        with connection.cursor() as cursor:
            from django.utils import timezone
            now = timezone.now()
            fields = list(kwargs.keys()) + ['created_at', 'updated_at']
            values = list(kwargs.values()) + [now, now]
            placeholders = ', '.join(['?' for _ in values])
            field_names = ', '.join(fields)
            cursor.execute(
                f"INSERT INTO {self.table_name} ({field_names}) VALUES ({placeholders})",
                values
            )
            return cursor.lastrowid
    
    def delete(self, id):
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {self.table_name} WHERE id = ?", [id])


class StoreImageManager:
    """Manager for store-specific Image operations"""
    def __init__(self, store_id):
        self.store_id = store_id
        self.table_name = f'store_{store_id}_images'
    
    def all(self):
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY created_at DESC")
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get(self, **kwargs):
        with connection.cursor() as cursor:
            conditions = []
            params = []
            for key, value in kwargs.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            where_clause = " AND ".join(conditions)
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE {where_clause}", params)
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if row:
                return dict(zip(columns, row))
            return None
    
    def filter(self, **kwargs):
        with connection.cursor() as cursor:
            conditions = []
            params = []
            for key, value in kwargs.items():
                if '__' in key:
                    field, lookup = key.split('__', 1)
                    if lookup == 'icontains':
                        conditions.append(f"{field} LIKE ?")
                        params.append(f"%{value}%")
                    else:
                        conditions.append(f"{field} = ?")
                        params.append(value)
                else:
                    conditions.append(f"{key} = ?")
                    params.append(value)
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE {where_clause} ORDER BY created_at DESC", params)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def create(self, **kwargs):
        with connection.cursor() as cursor:
            from django.utils import timezone
            now = timezone.now()
            fields = list(kwargs.keys()) + ['created_at', 'updated_at']
            values = list(kwargs.values()) + [now, now]
            placeholders = ', '.join(['?' for _ in values])
            field_names = ', '.join(fields)
            cursor.execute(
                f"INSERT INTO {self.table_name} ({field_names}) VALUES ({placeholders})",
                values
            )
            return cursor.lastrowid
    
    def update(self, id, **kwargs):
        with connection.cursor() as cursor:
            from django.utils import timezone
            set_clauses = []
            params = []
            for key, value in kwargs.items():
                set_clauses.append(f"{key} = ?")
                params.append(value)
            set_clauses.append("updated_at = ?")
            params.append(timezone.now())
            params.append(id)
            set_clause = ", ".join(set_clauses)
            cursor.execute(f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?", params)
    
    def delete(self, id):
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {self.table_name} WHERE id = ?", [id])
    
    def exists(self, **kwargs):
        with connection.cursor() as cursor:
            conditions = []
            params = []
            for key, value in kwargs.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            where_clause = " AND ".join(conditions)
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE {where_clause}", params)
            return cursor.fetchone()[0] > 0

