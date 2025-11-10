"""
Comprehensive test suite for store-specific table organization.
Tests that each store has its own isolated tables and all operations work correctly.
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

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.db import connection
from images.models import Store
from images.store_tables import create_store_tables, drop_store_tables
from images.store_helpers import StoreCategory, StoreProduct, StoreImage
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image as PILImage


class StoreTableOrganizationTest(TestCase):
    """Test store-specific table organization"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(username='testuser1', password='testpass123')
        self.user2 = User.objects.create_user(username='testuser2', password='testpass123')
        
        # Create test stores
        self.store1 = Store.objects.create(name='Test Store 1', user=self.user1)
        self.store2 = Store.objects.create(name='Test Store 2', user=self.user2)
        
        # Create tables for stores
        create_store_tables(self.store1.id)
        create_store_tables(self.store2.id)
        
        # Create test image file
        self.test_image = self.create_test_image()
    
    def create_test_image(self):
        """Create a test image file"""
        img = PILImage.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile('test_image.jpg', img_io.read(), content_type='image/jpeg')
    
    def test_store_tables_created(self):
        """Test that tables are created for each store"""
        with connection.cursor() as cursor:
            # Check store1 tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'store_1_%'")
            store1_tables = [row[0] for row in cursor.fetchall()]
            self.assertIn('store_1_categories', store1_tables)
            self.assertIn('store_1_products', store1_tables)
            self.assertIn('store_1_images', store1_tables)
            
            # Check store2 tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'store_2_%'")
            store2_tables = [row[0] for row in cursor.fetchall()]
            self.assertIn('store_2_categories', store2_tables)
            self.assertIn('store_2_products', store2_tables)
            self.assertIn('store_2_images', store2_tables)
    
    def test_category_isolation(self):
        """Test that categories are isolated per store"""
        # Create categories in store1
        cat1_store1 = StoreCategory.objects(self.store1.id).create(name='Electronics')
        cat2_store1 = StoreCategory.objects(self.store1.id).create(name='Clothing')
        
        # Create categories in store2
        cat1_store2 = StoreCategory.objects(self.store2.id).create(name='Electronics')
        cat2_store2 = StoreCategory.objects(self.store2.id).create(name='Food')
        
        # Verify store1 categories
        store1_cats = StoreCategory.objects(self.store1.id).all()
        self.assertEqual(len(store1_cats), 2)
        self.assertIn(cat1_store1.name, [c.name for c in store1_cats])
        self.assertIn(cat2_store1.name, [c.name for c in store1_cats])
        
        # Verify store2 categories
        store2_cats = StoreCategory.objects(self.store2.id).all()
        self.assertEqual(len(store2_cats), 2)
        self.assertIn(cat1_store2.name, [c.name for c in store2_cats])
        self.assertIn(cat2_store2.name, [c.name for c in store2_cats])
        
        # Verify IDs can overlap (same ID in different stores)
        self.assertEqual(cat1_store1.id, cat1_store2.id)  # Both have ID 1
        self.assertEqual(cat2_store1.id, cat2_store2.id)  # Both have ID 2
    
    def test_product_isolation(self):
        """Test that products are isolated per store"""
        # Create categories
        cat1_store1 = StoreCategory.objects(self.store1.id).create(name='Electronics')
        cat1_store2 = StoreCategory.objects(self.store2.id).create(name='Electronics')
        
        # Create products in store1
        prod1_store1 = StoreProduct.objects(self.store1.id).create(
            category=cat1_store1,
            name='iPhone 15'
        )
        prod2_store1 = StoreProduct.objects(self.store1.id).create(
            category=cat1_store1,
            name='Samsung Galaxy'
        )
        
        # Create products in store2
        prod1_store2 = StoreProduct.objects(self.store2.id).create(
            category=cat1_store2,
            name='iPhone 15'
        )
        prod2_store2 = StoreProduct.objects(self.store2.id).create(
            category=cat1_store2,
            name='MacBook Pro'
        )
        
        # Verify store1 products
        store1_prods = StoreProduct.objects(self.store1.id).all()
        self.assertEqual(len(store1_prods), 2)
        self.assertIn(prod1_store1.name, [p.name for p in store1_prods])
        self.assertIn(prod2_store1.name, [p.name for p in store1_prods])
        
        # Verify store2 products
        store2_prods = StoreProduct.objects(self.store2.id).all()
        self.assertEqual(len(store2_prods), 2)
        self.assertIn(prod1_store2.name, [p.name for p in store2_prods])
        self.assertIn(prod2_store2.name, [p.name for p in store2_prods])
        
        # Verify products from store1 don't appear in store2
        store2_prod_names = [p.name for p in store2_prods]
        self.assertNotIn(prod2_store1.name, store2_prod_names)
    
    def test_image_isolation(self):
        """Test that images are isolated per store"""
        # Create categories and products
        cat1_store1 = StoreCategory.objects(self.store1.id).create(name='Electronics')
        cat1_store2 = StoreCategory.objects(self.store2.id).create(name='Electronics')
        
        prod1_store1 = StoreProduct.objects(self.store1.id).create(
            category=cat1_store1,
            name='iPhone 15'
        )
        prod1_store2 = StoreProduct.objects(self.store2.id).create(
            category=cat1_store2,
            name='iPhone 15'
        )
        
        # Create images in store1
        img1_store1 = StoreImage.objects(self.store1.id).create(
            product=prod1_store1,
            name='iPhone Front',
            image_file=self.test_image,
            image_code='iphone_front'
        )
        img2_store1 = StoreImage.objects(self.store1.id).create(
            product=prod1_store1,
            name='iPhone Back',
            image_file=self.test_image,
            image_code='iphone_back'
        )
        
        # Create images in store2
        img1_store2 = StoreImage.objects(self.store2.id).create(
            product=prod1_store2,
            name='iPhone Front',
            image_file=self.test_image,
            image_code='iphone_front'
        )
        
        # Verify store1 images
        store1_imgs = StoreImage.objects(self.store1.id).all()
        self.assertEqual(len(store1_imgs), 2)
        self.assertIn(img1_store1.image_code, [i.image_code for i in store1_imgs])
        self.assertIn(img2_store1.image_code, [i.image_code for i in store1_imgs])
        
        # Verify store2 images
        store2_imgs = StoreImage.objects(self.store2.id).all()
        self.assertEqual(len(store2_imgs), 1)
        self.assertIn(img1_store2.image_code, [i.image_code for i in store2_imgs])
        
        # Verify image codes can be the same in different stores
        self.assertEqual(img1_store1.image_code, img1_store2.image_code)
    
    def test_image_code_uniqueness_per_store(self):
        """Test that image codes are unique within a store but can overlap across stores"""
        cat1_store1 = StoreCategory.objects(self.store1.id).create(name='Electronics')
        prod1_store1 = StoreProduct.objects(self.store1.id).create(
            category=cat1_store1,
            name='iPhone 15'
        )
        
        # Create image with code 'test_code'
        img1 = StoreImage.objects(self.store1.id).create(
            product=prod1_store1,
            name='Image 1',
            image_file=self.test_image,
            image_code='test_code'
        )
        
        # Try to create another image with same code in same store - should fail or auto-increment
        img2 = StoreImage.objects(self.store1.id).create(
            product=prod1_store1,
            name='Image 2',
            image_file=self.test_image,
            image_code='test_code'  # Same code
        )
        
        # The second image should have a modified code (test_code_1)
        self.assertNotEqual(img1.image_code, img2.image_code)
        self.assertTrue(img2.image_code.startswith('test_code'))
    
    def test_crud_operations(self):
        """Test CRUD operations on store-specific tables"""
        # CREATE
        cat1 = StoreCategory.objects(self.store1.id).create(name='Test Category')
        self.assertIsNotNone(cat1.id)
        self.assertEqual(cat1.name, 'Test Category')
        
        # READ
        retrieved = StoreCategory.objects(self.store1.id).get(id=cat1.id)
        self.assertEqual(retrieved.name, 'Test Category')
        
        # UPDATE
        cat1.name = 'Updated Category'
        cat1.save()
        updated = StoreCategory.objects(self.store1.id).get(id=cat1.id)
        self.assertEqual(updated.name, 'Updated Category')
        
        # DELETE
        cat1.delete()
        with self.assertRaises(Exception):
            StoreCategory.objects(self.store1.id).get(id=cat1.id)
    
    def test_foreign_key_relationships(self):
        """Test that foreign key relationships work correctly"""
        # Create category
        cat1 = StoreCategory.objects(self.store1.id).create(name='Electronics')
        
        # Create product linked to category
        prod1 = StoreProduct.objects(self.store1.id).create(
            category=cat1,
            name='iPhone 15'
        )
        
        # Verify relationship
        self.assertEqual(prod1.category_id, cat1.id)
        self.assertEqual(prod1.category.name, cat1.name)
        
        # Create image linked to product
        img1 = StoreImage.objects(self.store1.id).create(
            product=prod1,
            name='iPhone Front',
            image_file=self.test_image,
            image_code='iphone_front'
        )
        
        # Verify relationship
        self.assertEqual(img1.product_id, prod1.id)
        self.assertEqual(img1.product.name, prod1.name)
        self.assertEqual(img1.product.category.name, cat1.name)
    
    def test_cascade_deletion(self):
        """Test that cascade deletion works correctly"""
        # Create category, product, and image
        cat1 = StoreCategory.objects(self.store1.id).create(name='Electronics')
        prod1 = StoreProduct.objects(self.store1.id).create(
            category=cat1,
            name='iPhone 15'
        )
        img1 = StoreImage.objects(self.store1.id).create(
            product=prod1,
            name='iPhone Front',
            image_file=self.test_image,
            image_code='iphone_front'
        )
        
        # Delete category - should cascade to products and images
        cat1.delete()
        
        # Verify cascade deletion
        with self.assertRaises(Exception):
            StoreProduct.objects(self.store1.id).get(id=prod1.id)
        with self.assertRaises(Exception):
            StoreImage.objects(self.store1.id).get(id=img1.id)
    
    def test_filtering_and_search(self):
        """Test filtering and search operations"""
        # Create test data
        cat1 = StoreCategory.objects(self.store1.id).create(name='Electronics')
        cat2 = StoreCategory.objects(self.store1.id).create(name='Clothing')
        
        prod1 = StoreProduct.objects(self.store1.id).create(category=cat1, name='iPhone')
        prod2 = StoreProduct.objects(self.store1.id).create(category=cat1, name='iPad')
        prod3 = StoreProduct.objects(self.store1.id).create(category=cat2, name='T-Shirt')
        
        # Test filtering by category
        electronics_products = StoreProduct.objects(self.store1.id).filter(category_id=cat1.id)
        self.assertEqual(len(electronics_products), 2)
        
        # Test name search (icontains)
        phone_products = StoreProduct.objects(self.store1.id).filter(name__icontains='Phone')
        self.assertEqual(len(phone_products), 1)
        self.assertEqual(phone_products[0].name, 'iPhone')
    
    def test_multiple_stores_same_data(self):
        """Test that multiple stores can have the same data without conflicts"""
        # Create identical structure in both stores
        cat1_store1 = StoreCategory.objects(self.store1.id).create(name='Electronics')
        cat1_store2 = StoreCategory.objects(self.store2.id).create(name='Electronics')
        
        prod1_store1 = StoreProduct.objects(self.store1.id).create(
            category=cat1_store1,
            name='iPhone 15'
        )
        prod1_store2 = StoreProduct.objects(self.store2.id).create(
            category=cat1_store2,
            name='iPhone 15'
        )
        
        img1_store1 = StoreImage.objects(self.store1.id).create(
            product=prod1_store1,
            name='Front View',
            image_file=self.test_image,
            image_code='front_view'
        )
        img1_store2 = StoreImage.objects(self.store2.id).create(
            product=prod1_store2,
            name='Front View',
            image_file=self.test_image,
            image_code='front_view'
        )
        
        # Verify both stores have their own data
        self.assertEqual(len(StoreCategory.objects(self.store1.id).all()), 1)
        self.assertEqual(len(StoreCategory.objects(self.store2.id).all()), 1)
        self.assertEqual(len(StoreProduct.objects(self.store1.id).all()), 1)
        self.assertEqual(len(StoreProduct.objects(self.store2.id).all()), 1)
        self.assertEqual(len(StoreImage.objects(self.store1.id).all()), 1)
        self.assertEqual(len(StoreImage.objects(self.store2.id).all()), 1)
        
        # Verify data is isolated
        store1_prod = StoreProduct.objects(self.store1.id).get(id=prod1_store1.id)
        store2_prod = StoreProduct.objects(self.store2.id).get(id=prod1_store2.id)
        self.assertEqual(store1_prod.name, store2_prod.name)
        self.assertNotEqual(store1_prod.id, store2_prod.id)  # Different IDs in different tables
    
    def tearDown(self):
        """Clean up test data"""
        # Drop test tables
        try:
            drop_store_tables(self.store1.id)
            drop_store_tables(self.store2.id)
        except:
            pass


class StoreTableIntegrationTest(TestCase):
    """Integration tests for store table system"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_store_creation_creates_tables(self):
        """Test that creating a store automatically creates its tables"""
        # Create store via form
        response = self.client.post('/stores/create/', {
            'name': 'New Test Store'
        })
        
        # Get the created store
        store = Store.objects.get(name='New Test Store')
        
        # Verify tables were created
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", 
                          [f'store_{store.id}_%'])
            tables = [row[0] for row in cursor.fetchall()]
            self.assertIn(f'store_{store.id}_categories', tables)
            self.assertIn(f'store_{store.id}_products', tables)
            self.assertIn(f'store_{store.id}_images', tables)
    
    def test_category_creation_uses_store_tables(self):
        """Test that category creation uses store-specific tables"""
        # Create store and tables
        store = Store.objects.create(name='Test Store', user=self.user)
        create_store_tables(store.id)
        
        # Create category via form
        response = self.client.post(f'/categories/create/{store.id}/', {
            'name': 'Test Category'
        })
        
        # Verify category exists in store-specific table
        categories = StoreCategory.objects(store.id).filter(name='Test Category')
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0].name, 'Test Category')
    
    def test_product_creation_uses_store_tables(self):
        """Test that product creation uses store-specific tables"""
        # Create store, category, and tables
        store = Store.objects.create(name='Test Store', user=self.user)
        create_store_tables(store.id)
        category = StoreCategory.objects(store.id).create(name='Electronics')
        
        # Create product via form
        response = self.client.post(f'/stores/{store.id}/categories/{category.id}/products/create/', {
            'name': 'iPhone 15'
        })
        
        # Verify product exists in store-specific table
        products = StoreProduct.objects(store.id).filter(name='iPhone 15')
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, 'iPhone 15')
        self.assertEqual(products[0].category_id, category.id)


def run_tests():
    """Run all tests"""
    import unittest
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(StoreTableOrganizationTest))
    suite.addTests(loader.loadTestsFromTestCase(StoreTableIntegrationTest))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"\n{test}:")
            print(traceback)
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"\n{test}:")
            print(traceback)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

