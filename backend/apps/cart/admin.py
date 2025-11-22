from django.contrib import admin
from apps.cart.models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['added_at', 'total_price']
    fields = ['product', 'quantity', 'total_price', 'added_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_total_items', 'get_total_amount', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CartItemInline]

    def get_total_items(self, obj):
        return obj.total_items
    get_total_items.short_description = 'Всего товаров'

    def get_total_amount(self, obj):
        return f"{obj.total_amount} руб."
    get_total_amount.short_description = 'Общая сумма'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'get_unit_price', 'get_total_price', 'added_at']
    list_filter = ['added_at', 'cart__user']
    search_fields = ['product__name', 'cart__user__username']
    readonly_fields = ['added_at']

    def get_unit_price(self, obj):
        return f"{obj.product.price} руб."
    get_unit_price.short_description = 'Цена за единицу'

    def get_total_price(self, obj):
        return f"{obj.total_price} руб."
    get_total_price.short_description = 'Общая стоимость'
