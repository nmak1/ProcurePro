# apps/products/admin.py
from django.contrib import admin
from apps.products.models import Category, Product, ProductCharacteristic
# УБРАТЬ ProductImage и ProductReview ↑

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'display_order', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'supplier', 'price', 'is_available']
    list_filter = ['category', 'supplier', 'is_available']
    search_fields = ['name', 'sku']

@admin.register(ProductCharacteristic)
class ProductCharacteristicAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'value']
    list_filter = ['product']
