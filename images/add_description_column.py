"""
Migration script to add description column to existing product tables
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

def add_description_column_to_store(store_id):
    """Add description column to a specific store's products table"""
    with connection.cursor() as cursor:
        table_name = f'store_{store_id}_products'
        
        # Check if column already exists
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add description if it doesn't exist
        if 'description' not in columns:
            try:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN description TEXT")
                print(f"✓ Added description column to {table_name}")
            except Exception as e:
                print(f"✗ Error adding description to {table_name}: {e}")
        else:
            print(f"  description column already exists in {table_name}")

# Add description column to all existing stores
stores = Store.objects.all()
print("Adding description column to existing product tables...")
print("="*70)

for store in stores:
    print(f"\nStore {store.id} ({store.name}):")
    add_description_column_to_store(store.id)

print("="*70)
print("Done!")

