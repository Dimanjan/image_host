"""
Migration script to add price columns to existing product tables
"""
import os
import sys
import django
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'imagehost.settings')
django.setup()

from django.db import connection
from images.models import Store

def add_price_columns_to_store(store_id):
    """Add price columns to a specific store's products table"""
    with connection.cursor() as cursor:
        table_name = f'store_{store_id}_products'
        
        # Check if columns already exist
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add marked_price if it doesn't exist
        if 'marked_price' not in columns:
            try:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN marked_price DECIMAL(10, 2)")
                print(f"✓ Added marked_price column to {table_name}")
            except Exception as e:
                print(f"✗ Error adding marked_price to {table_name}: {e}")
        else:
            print(f"  marked_price column already exists in {table_name}")
        
        # Add min_discounted_price if it doesn't exist
        if 'min_discounted_price' not in columns:
            try:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN min_discounted_price DECIMAL(10, 2)")
                print(f"✓ Added min_discounted_price column to {table_name}")
            except Exception as e:
                print(f"✗ Error adding min_discounted_price to {table_name}: {e}")
        else:
            print(f"  min_discounted_price column already exists in {table_name}")

# Add price columns to all existing stores
stores = Store.objects.all()
print("Adding price columns to existing product tables...")
print("="*70)

for store in stores:
    print(f"\nStore {store.id} ({store.name}):")
    add_price_columns_to_store(store.id)

print("="*70)
print("Done!")

