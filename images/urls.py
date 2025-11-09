from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.store_list, name='store_list'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('stores/create/', views.store_create, name='store_create'),
    path('stores/<int:store_id>/', views.store_detail, name='store_detail'),
    path('categories/create/<int:store_id>/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
    path('products/create/<int:category_id>/', views.product_create, name='product_create'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('images/<int:image_id>/update/', views.image_update, name='image_update'),
    path('images/<int:image_id>/delete/', views.image_delete, name='image_delete'),
    path('image/<str:store_name>/<str:category_name>/<str:product_name>/<str:image_code>/', views.image_view, name='image_view'),
    path('api/search-product/', views.api_search_product, name='api_search_product'),
    path('api-test/', views.api_test_page, name='api_test_page'),
]

