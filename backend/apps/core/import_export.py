import yaml
import os
from django.db import transaction
from backend.apps.products.models import Product, Category, ProductCharacteristic
from backend.apps.suppliers.models import Supplier
from django.contrib.auth import get_user_model

User = get_user_model()


class ProductImporter:
    def __init__(self):
        self.stats = {
            'created': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }

    def import_from_yaml(self, file_path):
        """Импорт товаров из YAML файла"""
        try:
            # Проверяем существует ли файл
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)

            if not data:
                raise ValueError("YAML file is empty or invalid")

            with transaction.atomic():
                self._process_data(data)

            return self.stats

        except Exception as e:
            self.stats['errors'] += 1
            raise Exception(f"Import failed: {str(e)}")

    def _process_data(self, data):
        """Обработка данных из YAML"""
        suppliers_data = data.get('suppliers', [])
        if not suppliers_data:
            raise ValueError("No suppliers found in YAML file")

        for supplier_data in suppliers_data:
            supplier = self._get_or_create_supplier(supplier_data)

            products_data = supplier_data.get('products', [])
            for product_data in products_data:
                self._create_product(product_data, supplier)

    def _get_or_create_supplier(self, supplier_data):
        """Создание или получение поставщика"""
        supplier_name = supplier_data.get('name')
        if not supplier_name:
            self.stats['errors'] += 1
            raise ValueError("Supplier name is required")

        # Создаем пользователя для поставщика
        email = supplier_data.get('email', f"{supplier_name.lower().replace(' ', '_')}@example.com")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': supplier_name.lower().replace(' ', '_'),
                'is_supplier': True,
                'first_name': supplier_name
            }
        )

        if created:
            user.set_password('temp_password_123')
            user.save()

        supplier, created = Supplier.objects.get_or_create(
            user=user,
            defaults={
                'name': supplier_name,
                'type': supplier_data.get('type', 'retail'),
                'email': email,
                'phone': supplier_data.get('phone', ''),
                'address': supplier_data.get('address', ''),
                'is_active': supplier_data.get('is_active', True),
                'accepts_orders': supplier_data.get('accepts_orders', True),
            }
        )

        return supplier

    def _create_product(self, product_data, supplier):
        """Создание или обновление товара"""
        product_name = product_data.get('name')
        if not product_name:
            self.stats['skipped'] += 1
            return

        category_name = product_data.get('category', 'General')
        category = self._get_or_create_category(category_name)

        try:
            product, created = Product.objects.update_or_create(
                name=product_name,
                supplier=supplier,
                defaults={
                    'description': product_data.get('description', ''),
                    'category': category,
                    'price': product_data.get('price', 0),
                    'min_order_quantity': product_data.get('min_order_quantity', 1),
                    'max_order_quantity': product_data.get('max_order_quantity', 100),
                    'is_available': product_data.get('is_available', True),
                }
            )

            if created:
                self.stats['created'] += 1
            else:
                self.stats['updated'] += 1

            # Обрабатываем характеристики
            characteristics = product_data.get('characteristics', [])
            self._update_characteristics(product, characteristics)

        except Exception as e:
            self.stats['errors'] += 1
            print(f"Error creating product {product_name}: {str(e)}")

    def _get_or_create_category(self, category_name):
        """Создание или получение категории"""
        category, created = Category.objects.get_or_create(
            name=category_name
        )
        return category

    def _update_characteristics(self, product, characteristics):
        """Обновление характеристик товара"""
        # Удаляем существующие характеристики
        product.characteristics.all().delete()

        # Добавляем новые характеристики
        for char_data in characteristics:
            if isinstance(char_data, dict) and 'name' in char_data and 'value' in char_data:
                ProductCharacteristic.objects.create(
                    product=product,
                    name=char_data['name'],
                    value=char_data['value']
                )