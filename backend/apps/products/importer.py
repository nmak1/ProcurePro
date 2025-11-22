
import yaml
from django.core.files import File
from .models import Product, Category, ProductCharacteristic


class ProductImporter:
    def __init__(self, supplier):
        self.supplier = supplier

    def import_from_yaml(self, yaml_file_path):
        with open(yaml_file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

        for category_data in data.get('categories', []):
            self.import_category(category_data)

    def import_category(self, category_data):
        category, created = Category.objects.get_or_create(
            name=category_data['name'],
            defaults={'description': category_data.get('description', '')}
        )

        for product_data in category_data.get('goods', []):
            self.import_product(product_data, category)

    def import_product(self, product_data, category):
        product, created = Product.objects.update_or_create(
            sku=product_data['code'],
            supplier=self.supplier,
            defaults={
                'name': product_data['name'],
                'category': category,
                'price': product_data['price'],
                'quantity': product_data.get('quantity', 0),
                'description': product_data.get('description', ''),
            }
        )

        # Характеристики товара
        for param_name, param_value in product_data.get('parameters', {}).items():
            ProductCharacteristic.objects.update_or_create(
                product=product,
                name=param_name,
                defaults={'value': param_value}
            )