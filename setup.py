from setuptools import setup, find_packages

setup(
    name="procurepro",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Django>=4.2,<4.3',
        'djangorestframework>=3.14,<3.15',
        'django-cors-headers>=4.0,<4.1',
        'django-filter>=23.1,<23.2',
        'django-celery-beat>=2.5,<2.6',
        'celery>=5.3,<5.4',
        'redis>=4.5,<4.6',
        'Pillow>=10.0,<10.1',
        'python-decouple>=3.8,<3.9',
        'PyYAML>=6.0,<6.1',
    ],
    python_requires='>=3.8',
)