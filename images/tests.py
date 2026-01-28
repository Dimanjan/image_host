
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from images.models import Store
from images.store_tables import create_store_tables
from images.store_helpers import StoreCategory, StoreProduct

class SearchAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.store = Store.objects.create(name='Test Store', user=self.user)
        
        # Initialize dynamic tables
        create_store_tables(self.store.id)
        
        # Create Category
        self.category = StoreCategory(self.store.id)
        self.category.name = "General"
        self.category.save()
        
        # Create Products
        # 1. Kala Patthar Basketball (Specific)
        self.p1 = StoreProduct(self.store.id)
        self.p1.name = "Kala Patthar Basketball"
        self.p1.category_id = self.category.id
        self.p1.marked_price = 2500.00
        self.p1.min_discounted_price = 2000.00
        self.p1.created_by_id = self.user.id
        self.p1.save()
        
        # 2. Basketball (Generic)
        self.p2 = StoreProduct(self.store.id)
        self.p2.name = "Basketball"
        self.p2.category_id = self.category.id
        self.p2.marked_price = 1000.00
        self.p2.min_discounted_price = 900.00
        self.p2.created_by_id = self.user.id
        self.p2.save()
        
        # 3. Football (Target for typo)
        self.p3 = StoreProduct(self.store.id)
        self.p3.name = "Football"
        self.p3.category_id = self.category.id
        self.p3.marked_price = 1500.00
        self.p3.min_discounted_price = 1200.00
        self.p3.created_by_id = self.user.id
        self.p3.save()
        
        self.url = reverse('api_search_product')

    def test_search_typo_fotbal(self):
        """Test that 'fotbal' finds 'Football' (WRatio recall)"""
        response = self.client.post(self.url, {
            'store_id': self.store.id,
            'product_name': 'fotbal'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertGreater(data['count'], 0)
        found_names = [r['product_name'] for r in data['results']]
        self.assertIn('Football', found_names)

    def test_search_split_word(self):
        """Test that 'foot ball' finds 'Football' (WRatio recall)"""
        response = self.client.post(self.url, {
            'store_id': self.store.id,
            'product_name': 'foot ball'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('Football', [r['product_name'] for r in data['results']])

    def test_search_ranking_specificity(self):
        """Test that 'basketball kala patthar' ranks 'Kala Patthar Basketball' #1 over 'Basketball'"""
        response = self.client.post(self.url, {
            'store_id': self.store.id,
            'product_name': 'basketball kala patthar'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        results = data['results']
        
        # Must find both
        found_names = [r['product_name'] for r in results]
        self.assertIn('Kala Patthar Basketball', found_names)
        self.assertIn('Basketball', found_names)
        
        # Specific match should be first
        self.assertEqual(results[0]['product_name'], 'Kala Patthar Basketball')

    def test_price_filtering(self):
        """Test Min/Max Price filtering"""
        # Search "ball" -> finds all 3
        
        # Filter: Min 1500. 
        # P1 (2000) -> Keep
        # P2 (900) -> Drop
        # P3 (1200) -> Drop
        response = self.client.post(self.url, {
            'store_id': self.store.id,
            'product_name': 'ball',
            'min_price': 1500
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        names = [r['product_name'] for r in data['results']]
        self.assertIn('Kala Patthar Basketball', names)
        self.assertNotIn('Football', names) # 1200 < 1500
        self.assertNotIn('Basketball', names) # 900 < 1500

    def test_sorting_price_asc(self):
        """Test Sorting by Price Low to High"""
        response = self.client.post(self.url, {
            'store_id': self.store.id,
            'product_name': 'ball',
            'sort': 'price_asc'
        })
        data = response.json()
        results = data['results']
        prices = [r.get('min_discounted_price') for r in results]
        # Should be [900, 1200, 2000]
        self.assertEqual(prices, sorted(prices))
        self.assertEqual(results[0]['product_name'], 'Basketball') # Cheapest

