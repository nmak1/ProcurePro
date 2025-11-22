from django.contrib import admin
from apps.suppliers.models import Supplier, SupplierContact


class SupplierContactInline(admin.TabularInline):
    model = SupplierContact
    extra = 1


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'accepts_orders', 'is_active', 'created_at')
    list_filter = ('accepts_orders', 'is_active', 'created_at')
    search_fields = ('name', 'user__username', 'user__email')
    readonly_fields = ('created_at',)
    inlines = [SupplierContactInline]


@admin.register(SupplierContact)
class SupplierContactAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'name', 'position', 'email', 'phone')
    list_filter = ('supplier',)
    search_fields = ('name', 'email', 'phone', 'supplier__name')
