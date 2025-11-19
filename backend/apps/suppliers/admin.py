from django.contrib import admin
from .models import Supplier, SupplierContact

class SupplierContactInline(admin.TabularInline):
    model = SupplierContact
    extra = 1

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'email', 'is_active', 'accepts_orders')
    list_filter = ('type', 'is_active', 'accepts_orders')
    search_fields = ('name', 'email')
    inlines = [SupplierContactInline]