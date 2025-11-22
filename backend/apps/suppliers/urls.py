from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.suppliers import views

app_name = 'suppliers'

router = DefaultRouter()
router.register(r'suppliers', views.SupplierViewSet, basename='supplier')
router.register(r'my-supplier', views.SupplierManagementViewSet, basename='supplier-management')

urlpatterns = [
    path('', include(router.urls)),
]
