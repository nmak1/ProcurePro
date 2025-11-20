from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, DeliveryAddressViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'delivery-addresses', DeliveryAddressViewSet, basename='delivery-address')

urlpatterns = [
    path('', include(router.urls)),
]