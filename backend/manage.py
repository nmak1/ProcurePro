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
        BASE_DIR / 'media' / 'products',
        BASE_DIR / 'media' / 'exports',
        BASE_DIR / 'media' / 'users',
        BASE_DIR / 'static',
        BASE_DIR / 'templates' / 'emails',
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

    import django
    django.setup()

    from django.contrib.auth import get_user_model
    from backend.apps.products.models import Category
    from backend.apps.suppliers.models import Supplier

    User = get_user_model()

    # Создаем базовые категории
    categories_data = [
        'Electronics',
        'Clothing',
        'Books',
        'Home & Garden',
        'Sports',
        'Toys',
        'Food & Beverages',
        'Health & Beauty'
    ]

    for category_name in categories_data:
        Category.objects.get_or_create(name=category_name)

    print("Sample categories created successfully!")


if __name__ == '__main__':
    # Дополнительные команды для manage.py
    if len(sys.argv) > 1 and sys.argv[1] == 'setup_dev':
        setup_sample_data()
    else:
        main()