# Store Table Organization Tests

This folder contains comprehensive tests for the store-specific table organization system.

## Test Coverage

### StoreTableOrganizationTest
Tests the core functionality of store-specific tables:

1. **Table Creation**: Verifies that tables are created for each store
2. **Data Isolation**: Tests that categories, products, and images are isolated per store
3. **Image Code Uniqueness**: Verifies image codes are unique within a store
4. **CRUD Operations**: Tests Create, Read, Update, Delete operations
5. **Foreign Key Relationships**: Tests relationships between categories, products, and images
6. **Cascade Deletion**: Tests that deleting a category cascades to products and images
7. **Filtering and Search**: Tests filtering and search operations
8. **Multiple Stores**: Tests that multiple stores can have identical data without conflicts

### StoreTableIntegrationTest
Integration tests that test the system through the web interface:

1. **Store Creation**: Tests that creating a store automatically creates its tables
2. **Category Creation**: Tests category creation via web forms
3. **Product Creation**: Tests product creation via web forms

## Running Tests

### Option 1: Run with Python
```bash
cd test_store_tables
python test_store_organization.py
```

### Option 2: Run with Django test runner
```bash
python manage.py test test_store_tables
```

### Option 3: Run specific test class
```bash
python manage.py test test_store_tables.StoreTableOrganizationTest
```

## Test Database

Tests use a separate test database (SQLite in memory) and clean up after themselves.
Each test creates its own store tables and cleans them up in `tearDown()`.

## Expected Results

All tests should pass, confirming:
- ✅ Each store has its own isolated tables
- ✅ Data from one store doesn't leak into another
- ✅ All CRUD operations work correctly
- ✅ Foreign key relationships work properly
- ✅ Cascade deletion works as expected
- ✅ Image codes are unique per store but can overlap across stores

