
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "imagehost.settings")
django.setup()

from django.db import connection
from images.models import Store

def add_url_column():
    """Add url column to all store image tables"""
    print("Starting migration to add 'url' column...")
    
    stores = Store.objects.all()
    count = 0
    updated = 0
    
    with connection.cursor() as cursor:
        for store in stores:
            table_name = f"store_{store.id}_images"
            print(f"Checking table {table_name}...")
            
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                print(f"Table {table_name} does not exist, skipping.")
                continue
                
            # Check if column exists
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "url" not in columns:
                print(f"Adding 'url' column to {table_name}...")
                try:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN url VARCHAR(500)")
                    updated += 1
                except Exception as e:
                    print(f"Error adding column to {table_name}: {e}")
            else:
                print(f"Column 'url' already exists in {table_name}.")
            
            # Also make sure image_file allows NULL (SQLite columns are nullable by default usually unless strict)
            # We can't easily alter column nullability in SQLite without recreating table, 
            # but standard ADD COLUMN creates nullable columns.
            # existing image_file columns might have NOT NULL constraint if created that way.
            # If so, we might need to handle that if we want to support 'only URL' images.
            # However, for now let's assume we can tolerate empty string or dummy value if strictly needed,
            # or rely on SQLite's lax typing if not in strict mode.
            
            count += 1
            
    print(f"\nMigration complete. Checked {count} stores. Updated {updated} tables.")

if __name__ == "__main__":
    add_url_column()
