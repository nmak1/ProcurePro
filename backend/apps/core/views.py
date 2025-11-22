from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from apps.core.import_export import ProductExporter, ProductImporter  # ← ИЗМЕНИТЕ ИМПОРТ
import os
from django.conf import settings


@api_view(['POST'])
@permission_classes([IsAdminUser])
def import_products(request):
    """API для импорта товаров"""
    try:
        file = request.FILES.get('file')
        supplier_id = request.data.get('supplier_id')

        if not file:
            return Response(
                {'error': 'Файл не предоставлен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Сохраняем временный файл
        file_path = os.path.join(settings.MEDIA_ROOT, 'temp', file.name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Импортируем товары
        importer = ProductImporter()
        stats = importer.import_from_file(file_path, supplier_id)

        # Удаляем временный файл
        os.remove(file_path)

        return Response({
            'detail': 'Импорт завершен',
            'stats': stats
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def supplier_import_products(request):
    """API для импорта товаров поставщиком"""
    try:
        if not hasattr(request.user, 'supplier_profile'):
            return Response(
                {'error': 'Доступно только для поставщиков'},
                status=status.HTTP_403_FORBIDDEN
            )

        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'Файл не предоставлен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Сохраняем временный файл
        file_path = os.path.join(settings.MEDIA_ROOT, 'temp', file.name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Импортируем товары для этого поставщика
        importer = ProductImporter()
        stats = importer.import_from_file(file_path, request.user.supplier_profile.id)

        # Удаляем временный файл
        os.remove(file_path)

        return Response({
            'detail': 'Импорт завершен',
            'stats': stats
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
