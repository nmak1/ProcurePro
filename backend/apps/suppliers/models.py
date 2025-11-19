from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Supplier(models.Model):
    SUPPLIER_TYPES = [
        ('factory', 'Factory'),
        ('retail', 'Retail Network'),
        ('entrepreneur', 'Individual Entrepreneur'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supplier_profile')
    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=20, choices=SUPPLIER_TYPES)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    is_active = models.BooleanField(default=True)
    accepts_orders = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class SupplierContact(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name} - {self.supplier.name}"