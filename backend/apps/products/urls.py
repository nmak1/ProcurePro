from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.products import views

app_name = 'products'

router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'categories', views.CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
]
