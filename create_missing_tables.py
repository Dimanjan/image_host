"""
Script to create tables for existing stores that don't have them
"""

import os
import sys
from pathlib import Path

import django

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "imagehost.settings")
django.setup()

from django.db import connection

from images.models import Store
from images.store_tables import create_store_tables

# Create tables for all existing stores that don't have them
stores = Store.objects.all()
print("Creating tables for existing stores...")
print("=" * 70)

for store in stores:
    with connection.cursor() as cursor:
        # Check if categories table exists
        table_name = f"store_{store.id}_categories"
        sql = (
            "SELECT name FROM sqlite_master WHERE type='table' AND name = '{}'".format(
                table_name
            )
        )
        cursor.execute(sql)
        if not cursor.fetchone():
            print(f"Creating tables for store {store.id} ({store.name})...")
            try:
                create_store_tables(store.id)
                print(f"✓ Created tables for store {store.id} ({store.name})")
            except Exception as e:
                print(f"✗ Error creating tables for store {store.id}: {e}")
        else:
            print(f"✓ Store {store.id} ({store.name}) already has tables")

print("=" * 70)
print("Done!")
