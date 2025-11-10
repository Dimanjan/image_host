"""
Simple manual test script for store-specific tables.
Run this to verify the system works correctly.
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

from django.contrib.auth.models import User
from django.db import connection
from images.models import Store
from images.store_tables import create_store_tables
from images.store_helpers import StoreCategory, StoreProduct, StoreImage
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image as PILImage


def create_test_image():
    """Create a test image file"""
    img = PILImage.new('RGB', (100, 100), color='red')
    img_io = BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)
    return SimpleUploadedFile('test_image.jpg', img_io.read(), content_type='image/jpeg')


def test_store_tables():
    """Test store-specific table creation and operations"""
    print("="*70)
    print("TESTING STORE-SPECIFIC TABLE ORGANIZATION")
    print("="*70)
    
    # Create test user
    user, created = User.objects.get_or_create(username='testuser', defaults={'password': 'testpass123'})
    if created:
        user.set_password('testpass123')
        user.save()
        print("✓ Created test user")
    else:
        print("✓ Using existing test user")
    
    # Create stores
    store1, created = Store.objects.get_or_create(name='Test Store 1', defaults={'user': user})
    if created:
        print(f"✓ Created Store 1 (ID: {store1.id})")
    else:
        print(f"✓ Using existing Store 1 (ID: {store1.id})")
    
    store2, created = Store.objects.get_or_create(name='Test Store 2', defaults={'user': user})
    if created:
        print(f"✓ Created Store 2 (ID: {store2.id})")
    else:
        print(f"✓ Using existing Store 2 (ID: {store2.id})")
    
    # Create tables for stores
    print("\n--- Creating Tables ---")
    try:
        create_store_tables(store1.id)
        print(f"✓ Created tables for Store {store1.id}")
    except Exception as e:
        print(f"✗ Error creating tables for Store {store1.id}: {e}")
        return False
    
    try:
        create_store_tables(store2.id)
        print(f"✓ Created tables for Store {store2.id}")
    except Exception as e:
        print(f"✗ Error creating tables for Store {store2.id}: {e}")
        return False
    
    # Verify tables exist
    print("\n--- Verifying Tables ---")
    with connection.cursor() as cursor:
        # Use string formatting instead of parameterized query to avoid Django debug issues
        pattern1 = f'store_{store1.id}_%'
        sql1 = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '{}'".format(pattern1.replace('%', '%%'))
        cursor.execute(sql1)
        store1_tables = [row[0] for row in cursor.fetchall()]
        print(f"Store {store1.id} tables: {store1_tables}")
        
        pattern2 = f'store_{store2.id}_%'
        sql2 = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '{}'".format(pattern2.replace('%', '%%'))
        cursor.execute(sql2)
        store2_tables = [row[0] for row in cursor.fetchall()]
        print(f"Store {store2.id} tables: {store2_tables}")
        
        if len(store1_tables) >= 3 and len(store2_tables) >= 3:
            print("✓ Tables created successfully")
        else:
            print("✗ Tables not created correctly")
            return False
    
    # Test category creation
    print("\n--- Testing Category Creation ---")
    try:
        cat1_store1 = StoreCategory.objects(store1.id).create(name='Electronics')
        print(f"✓ Created category '{cat1_store1.name}' in Store {store1.id} (ID: {cat1_store1.id})")
        
        cat1_store2 = StoreCategory.objects(store2.id).create(name='Electronics')
        print(f"✓ Created category '{cat1_store2.name}' in Store {store2.id} (ID: {cat1_store2.id})")
        
        # Verify isolation
        store1_cats = StoreCategory.objects(store1.id).all()
        store2_cats = StoreCategory.objects(store2.id).all()
        print(f"✓ Store {store1.id} has {len(store1_cats)} category(ies)")
        print(f"✓ Store {store2.id} has {len(store2_cats)} category(ies)")
        
        if len(store1_cats) == 1 and len(store2_cats) == 1:
            print("✓ Categories are isolated per store")
        else:
            print("✗ Category isolation failed")
            return False
    except Exception as e:
        print(f"✗ Error creating categories: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test product creation
    print("\n--- Testing Product Creation ---")
    try:
        prod1_store1 = StoreProduct.objects(store1.id).create(
            category=cat1_store1,
            name='iPhone 15'
        )
        print(f"✓ Created product '{prod1_store1.name}' in Store {store1.id}")
        
        prod1_store2 = StoreProduct.objects(store2.id).create(
            category=cat1_store2,
            name='iPhone 15'
        )
        print(f"✓ Created product '{prod1_store2.name}' in Store {store2.id}")
        
        # Verify isolation
        store1_prods = StoreProduct.objects(store1.id).all()
        store2_prods = StoreProduct.objects(store2.id).all()
        print(f"✓ Store {store1.id} has {len(store1_prods)} product(s)")
        print(f"✓ Store {store2.id} has {len(store2_prods)} product(s)")
        
        if len(store1_prods) == 1 and len(store2_prods) == 1:
            print("✓ Products are isolated per store")
        else:
            print("✗ Product isolation failed")
            return False
    except Exception as e:
        print(f"✗ Error creating products: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test image creation
    print("\n--- Testing Image Creation ---")
    try:
        test_image = create_test_image()
        
        img1_store1 = StoreImage.objects(store1.id).create(
            product=prod1_store1,
            name='iPhone Front',
            image_file=test_image,
            image_code='iphone_front'
        )
        print(f"✓ Created image '{img1_store1.name}' in Store {store1.id} (Code: {img1_store1.image_code})")
        
        img1_store2 = StoreImage.objects(store2.id).create(
            product=prod1_store2,
            name='iPhone Front',
            image_file=test_image,
            image_code='iphone_front'
        )
        print(f"✓ Created image '{img1_store2.name}' in Store {store2.id} (Code: {img1_store2.image_code})")
        
        # Verify isolation
        store1_imgs = StoreImage.objects(store1.id).all()
        store2_imgs = StoreImage.objects(store2.id).all()
        print(f"✓ Store {store1.id} has {len(store1_imgs)} image(s)")
        print(f"✓ Store {store2.id} has {len(store2_imgs)} image(s)")
        
        if len(store1_imgs) == 1 and len(store2_imgs) == 1:
            print("✓ Images are isolated per store")
        else:
            print("✗ Image isolation failed")
            return False
        
        # Verify same image codes can exist in different stores
        if img1_store1.image_code == img1_store2.image_code:
            print("✓ Same image codes can exist in different stores")
        else:
            print("✗ Image code isolation issue")
    except Exception as e:
        print(f"✗ Error creating images: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*70)
    print("ALL TESTS PASSED! ✓")
    print("="*70)
    return True


if __name__ == '__main__':
    success = test_store_tables()
    sys.exit(0 if success else 1)

