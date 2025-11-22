from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.cart import views

router = DefaultRouter()
router.register(r'cart', views.CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
    path('cart/items/add/', views.AddToCartView.as_view(), name='add-to-cart'),
    path('cart/items/<int:item_id>/update/', views.UpdateCartItemView.as_view(), name='update-cart-item'),
    path('cart/items/<int:item_id>/remove/', views.RemoveFromCartView.as_view(), name='remove-from-cart'),
]
