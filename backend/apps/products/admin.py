from django.contrib import admin
from .models import Category, Product, ProductCharacteristic, ProductImage

class ProductCharacteristicInline(admin.TabularInline):
    model = ProductCharacteristic
    extra = 1

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'supplier', 'price', 'is_available')
    list_filter = ('category', 'supplier', 'is_available')
    search_fields = ('name', 'description')
    inlines = [ProductCharacteristicInline, ProductImageInline]