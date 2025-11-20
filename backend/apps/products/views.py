from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('supplier', 'category').prefetch_related(
        'characteristics', 'images'
    ).filter(is_available=True)
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'supplier']
    search_fields = ['name', 'description', 'supplier__name']
    ordering_fields = ['price', 'name', 'created_at']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Фильтрация по минимальной цене
        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        # Фильтрация по максимальной цене
        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        category_id = request.query_params.get('category_id')
        if category_id:
            products = self.queryset.filter(category_id=category_id)
            serializer = self.get_serializer(products, many=True)
            return Response(serializer.data)
        return Response([])

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Популярные товары"""
        featured_products = self.queryset.order_by('-created_at')[:10]
        serializer = self.get_serializer(featured_products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        """Переключение доступности товара (для поставщиков)"""
        product = self.get_object()

        # Проверяем, что пользователь - поставщик этого товара
        if hasattr(request.user, 'supplier_profile') and product.supplier == request.user.supplier_profile:
            product.is_available = not product.is_available
            product.save()
            return Response({
                'status': 'success',
                'is_available': product.is_available,
                'message': f'Product availability set to {product.is_available}'
            })
        else:
            return Response(
                {'error': 'You do not have permission to modify this product'},
                status=status.HTTP_403_FORBIDDEN
            )


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.prefetch_related('children', 'products')
    serializer_class = CategorySerializer

    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        category = self.get_object()
        products = category.products.filter(is_available=True)

        # Пагинация
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Возвращает дерево категорий"""

        def get_category_tree(category):
            return {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'children': [get_category_tree(child) for child in category.children.all()]
            }

        root_categories = Category.objects.filter(parent__isnull=True)
        tree_data = [get_category_tree(cat) for cat in root_categories]
        return Response(tree_data)