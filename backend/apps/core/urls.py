from django.urls import path
from . import views

urlpatterns = [
    path('import-products/', views.import_products, name='import-products'),
    path('supplier-import/', views.supplier_import_products, name='supplier-import'),
]
