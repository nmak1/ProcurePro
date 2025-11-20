from django.urls import path
from .views import supplier_products, toggle_orders, supplier_orders

urlpatterns = [
    path('products/', supplier_products, name='supplier-products'),
    path('toggle-orders/', toggle_orders, name='toggle-orders'),
    path('orders/', supplier_orders, name='supplier-orders'),
]