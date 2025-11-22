from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.apps import apps
import random


class Command(BaseCommand):
    help = 'Создание тестовых данных для ProcurePro'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных...')

        # Получаем модели
        User = get_user_model()
        Category = apps.get_model('products', 'Category')
        Product = apps.get_model('products', 'Product')
        ProductCharacteristic = apps.get_model('products', 'ProductCharacteristic')
        Supplier = apps.get_model('suppliers', 'Supplier')
        Cart = apps.get_model('cart', 'Cart')

        # Создаем администратора
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@procurepro.com',
                'user_type': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Создан администратор: admin / admin123'))

        # Создаем поставщиков
        suppliers_data = [
            {
                'name': 'TechSupplier Inc.',
                'description': 'Поставщик электроники и техники',
                'user_data': {
                    'username': 'techsupplier',
                    'email': 'tech@supplier.com',
                    'user_type': 'supplier',
                    'first_name': 'Алексей',
                    'last_name': 'Иванов'
                }
            },
            {
                'name': 'OfficePro Ltd.',
                'description': 'Поставщик офисных товаров',
                'user_data': {
                    'username': 'officepro',
                    'email': 'office@pro.com',
                    'user_type': 'supplier',
                    'first_name': 'Мария',
                    'last_name': 'Петрова'
                }
            }
        ]

        suppliers = []
        for supplier_data in suppliers_data:
            user_data = supplier_data.pop('user_data')
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password('supplier123')
                user.save()

            supplier, created = Supplier.objects.get_or_create(
                user=user,
                defaults=supplier_data
            )
            suppliers.append(supplier)
            self.stdout.write(self.style.SUCCESS(f'Создан поставщик: {supplier.name}'))

        # Создаем категории
        categories_data = [
            {'name': 'Электроника', 'description': 'Электронные устройства и гаджеты'},
            {'name': 'Офисные товары', 'description': 'Товары для офиса'},
            {'name': 'Компьютеры и комплектующие', 'description': 'Компьютерная техника', 'parent': 'Электроника'},
            {'name': 'Смартфоны', 'description': 'Мобильные телефоны', 'parent': 'Электроника'},
            {'name': 'Канцелярия', 'description': 'Канцелярские товары', 'parent': 'Офисные товары'},
        ]

        categories = {}
        for cat_data in categories_data:
            parent_name = cat_data.pop('parent', None)
            parent = categories.get(parent_name) if parent_name else None

            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={**cat_data, 'parent': parent}
            )
            categories[cat_data['name']] = category
            self.stdout.write(self.style.SUCCESS(f'Создана категория: {category.name}'))

        # Создаем товары - используем только name для поиска
        products_data = [
            {
                'name': 'Ноутбук Dell XPS 13',
                'description': 'Мощный ультрабук с процессором Intel Core i7',
                'category': 'Компьютеры и комплектующие',
                'supplier': suppliers[0],
                'price': 89999,
                'quantity': 15,
                'characteristics': [
                    {'name': 'Процессор', 'value': 'Intel Core i7'},
                    {'name': 'Оперативная память', 'value': '16 ГБ'},
                    {'name': 'SSD', 'value': '512 ГБ'}
                ]
            },
            {
                'name': 'iPhone 15 Pro',
                'description': 'Флагманский смартфон Apple',
                'category': 'Смартфоны',
                'supplier': suppliers[0],
                'price': 129999,
                'quantity': 25,
                'characteristics': [
                    {'name': 'Память', 'value': '256 ГБ'},
                    {'name': 'Камера', 'value': '48 Мп'},
                    {'name': 'Экран', 'value': '6.1" Super Retina XDR'}
                ]
            },
            {
                'name': 'Офисный стул',
                'description': 'Эргономичный офисный стул с регулировкой высоты',
                'category': 'Офисные товары',
                'supplier': suppliers[1],
                'price': 8999,
                'quantity': 30,
                'characteristics': [
                    {'name': 'Материал', 'value': 'Ткань, металл'},
                    {'name': 'Цвет', 'value': 'Черный'},
                    {'name': 'Максимальная нагрузка', 'value': '120 кг'}
                ]
            },
            {
                'name': 'Набор ручек',
                'description': 'Набор гелевых ручек 6 цветов',
                'category': 'Канцелярия',
                'supplier': suppliers[1],
                'price': 299,
                'quantity': 100,
                'characteristics': [
                    {'name': 'Количество', 'value': '6 штук'},
                    {'name': 'Тип чернил', 'value': 'Гелевые'},
                    {'name': 'Цвета', 'value': 'Синий, черный, красный, зеленый, фиолетовый, оранжевый'}
                ]
            }
        ]

        for product_data in products_data:
            characteristics = product_data.pop('characteristics', [])
            category_name = product_data.pop('category')

            # Используем только name для поиска, остальные поля заполнятся автоматически
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults={
                    **product_data,
                    'category': categories[category_name]
                }
            )

            if created:
                for char_data in characteristics:
                    ProductCharacteristic.objects.create(
                        product=product,
                        name=char_data['name'],
                        value=char_data['value']
                    )

            self.stdout.write(self.style.SUCCESS(f'Создан товар: {product.name}'))

        # Создаем тестового клиента
        client, created = User.objects.get_or_create(
            username='client',
            defaults={
                'email': 'client@test.com',
                'user_type': 'client',
                'first_name': 'Иван',
                'last_name': 'Петров'
            }
        )
        if created:
            client.set_password('client123')
            client.save()
            # Создаем корзину для клиента
            Cart.objects.get_or_create(user=client)
            self.stdout.write(self.style.SUCCESS('Создан тестовый клиент: client / client123'))

        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы!'))
