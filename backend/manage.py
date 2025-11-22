#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'procurepro.settings')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Создаем необходимые директории при запуске
    create_necessary_directories()

    execute_from_command_line(sys.argv)


def create_necessary_directories():
    """Создает необходимые директории для проекта"""
    import os
    from pathlib import Path

    # Базовые директории
    BASE_DIR = Path(__file__).resolve().parent

    directories = [
        BASE_DIR / 'media' / 'imports',
        BASE_DIR / 'media' / 'exports',
        BASE_DIR / 'media' / 'products',
        BASE_DIR / 'media' / 'users',
        BASE_DIR / 'media' / 'categories',
        BASE_DIR / 'media' / 'temp',
        BASE_DIR / 'static',
        BASE_DIR / 'templates' / 'emails',
        BASE_DIR / 'backups',
        BASE_DIR / 'logs',
    ]

    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            # print(f"✓ Directory created: {directory}")  # Можно раскомментировать для отладки
        except Exception as e:
            print(f"✗ Error creating directory {directory}: {e}")


def setup_sample_data():
    """Создает пример данных для разработки"""
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'procurepro.settings')

    try:
        import django
        django.setup()

        from django.contrib.auth import get_user_model
        from apps.products.models import Category
        from apps.suppliers.models import Supplier

        User = get_user_model()

        # Создаем суперпользователя если не существует
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@procurepro.com',
                password='admin123',
                user_type='admin'
            )
            print("✓ Superuser created: admin / admin123")

        # Создаем базовые категории
        categories_data = [
            'Электроника',
            'Одежда',
            'Книги',
            'Дом и сад',
            'Спорт',
            'Игрушки',
            'Продукты питания',
            'Здоровье и красота'
        ]

        for category_name in categories_data:
            Category.objects.get_or_create(name=category_name)

        print("✓ Sample categories created successfully!")

        # Создаем тестового поставщика
        if not User.objects.filter(username='supplier1').exists():
            supplier_user = User.objects.create_user(
                username='supplier1',
                email='supplier@example.com',
                password='supplier123',
                user_type='supplier',
                first_name='Иван',
                last_name='Поставщиков'
            )

            Supplier.objects.create(
                user=supplier_user,
                name='Тестовый поставщик ООО',
                description='Поставщик тестовых товаров',
                type='wholesale'
            )
            print("✓ Sample supplier created: supplier1 / supplier123")

        # Создаем тестового клиента
        if not User.objects.filter(username='client1').exists():
            User.objects.create_user(
                username='client1',
                email='client@example.com',
                password='client123',
                user_type='client',
                first_name='Петр',
                last_name='Клиентов'
            )
            print("✓ Sample client created: client1 / client123")

        print("\n🎯 Development setup completed!")
        print("Available test accounts:")
        print("  Admin:     admin / admin123")
        print("  Supplier:  supplier1 / supplier123")
        print("  Client:    client1 / client123")

    except Exception as e:
        print(f"✗ Error setting up sample data: {e}")


def check_system_health():
    """Проверяет здоровье системы"""
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'procurepro.settings')

    try:
        import django
        django.setup()

        from django.db import connection
        from django.core.cache import cache
        from django.contrib.auth import get_user_model

        User = get_user_model()

        print("🔍 System Health Check:")

        # Проверка базы данных
        try:
            connection.ensure_connection()
            print("✓ Database: OK")
        except Exception as e:
            print(f"✗ Database: ERROR - {e}")

        # Проверка кеша
        try:
            cache.set('health_check', 'ok', 1)
            if cache.get('health_check') == 'ok':
                print("✓ Cache: OK")
            else:
                print("✗ Cache: ERROR")
        except Exception as e:
            print(f"✗ Cache: ERROR - {e}")

        # Статистика
        print(f"✓ Users: {User.objects.count()}")

        from apps.products.models import Product, Category
        from apps.suppliers.models import Supplier
        from apps.orders.models import Order

        print(f"✓ Categories: {Category.objects.count()}")
        print(f"✓ Suppliers: {Supplier.objects.count()}")
        print(f"✓ Products: {Product.objects.count()}")
        print(f"✓ Orders: {Order.objects.count()}")

        print("\n🎯 System is healthy!")

    except Exception as e:
        print(f"✗ Health check failed: {e}")


if __name__ == '__main__':
    # Дополнительные команды для manage.py
    if len(sys.argv) > 1:
        if sys.argv[1] == 'setup_dev':
            setup_sample_data()
        elif sys.argv[1] == 'health_check':
            check_system_health()
        else:
            main()
    else:
        main()
