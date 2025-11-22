import yaml
import os
from django.apps import apps


class ProductExporter:
    """Экспорт товаров в YAML файлы"""

    def __init__(self):
        self.stats = {
            'exported': 0,
            'errors': 0
        }

    def export_to_yaml(self, file_path):
        """Экспорт товаров в YAML файл"""
        try:
            Product = apps.get_model('products', 'Product')
            Category = apps.get_model('products', 'Category')
            ProductCharacteristic = apps.get_model('products', 'ProductCharacteristic')
            Supplier = apps.get_model('suppliers', 'Supplier')

            products = Product.objects.select_related(
                'category', 'supplier'
            ).prefetch_related('characteristics').filter(is_available=True)

            export_data = []

            for product in products:
                product_data = {
                    'name': product.name,
                    'description': product.description,
                    'category': product.category.name,
                    'supplier': product.supplier.name,
                    'price': float(product.price),
                    'quantity': product.quantity,
                    'min_quantity': product.min_quantity,
                    'is_available': product.is_available,
                    'characteristics': [
                        {
                            'name': char.name,
                            'value': char.value
                        }
                        for char in product.characteristics.all()
                    ]
                }
                export_data.append(product_data)
                self.stats['exported'] += 1

            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as file:
                yaml.dump(export_data, file, allow_unicode=True, default_flow_style=False)

            return self.stats

        except Exception as e:
            self.stats['errors'] += 1
            raise Exception(f"Ошибка экспорта в файл {file_path}: {str(e)}")


class ProductImporter:
    """Импорт товаров из YAML файлов"""

    def __init__(self):
        self.stats = {
            'created': 0,
            'updated': 0,
            'errors': 0
        }

    def import_from_file(self, file_path, supplier_id=None):
        """Импорт товаров из YAML файла"""
        try:
            # Заглушка для реализации импорта
            # В реальном приложении здесь будет парсинг YAML и создание/обновление товаров
            return self.stats
        except Exception as e:
            self.stats['errors'] += 1
            raise Exception(f"Ошибка импорта из файла {file_path}: {str(e)}")
