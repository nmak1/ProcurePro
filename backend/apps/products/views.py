from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from apps.products.models import Product, Category, ProductReview
from apps.products.serializers import (
    ProductSerializer, CategorySerializer, ProductListSerializer, ProductReviewSerializer
)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_available=True).select_related(
        'category', 'supplier'
    ).prefetch_related(
        'characteristics', 'images', 'reviews'
    )
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'supplier', 'is_featured', 'is_new']
    search_fields = ['name', 'description', 'short_description', 'sku']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer

    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        """Получить похожие товары"""
        product = self.get_object()
        similar_products = Product.objects.filter(
            category=product.category,
            is_available=True
        ).exclude(id=product.id)[:8]

        serializer = ProductListSerializer(similar_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Рекомендуемые товары"""
        featured_products = Product.objects.filter(
            is_featured=True,
            is_available=True
        )[:12]

        serializer = ProductListSerializer(featured_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def new(self, request):
        """Новые товары"""
        new_products = Product.objects.filter(
            is_new=True,
            is_available=True
        )[:12]

        serializer = ProductListSerializer(new_products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def reviews(self, request, pk=None):
        """Получить или добавить отзывы к товару"""
        product = self.get_object()

        if request.method == 'GET':
            reviews = product.reviews.filter(is_approved=True)
            serializer = ProductReviewSerializer(reviews, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            if not request.user.is_authenticated:
                return Response(
                    {'error': 'Требуется авторизация'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Проверяем, не оставлял ли пользователь уже отзыв
            if product.reviews.filter(user=request.user).exists():
                return Response(
                    {'error': 'Вы уже оставляли отзыв на этот товар'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = ProductReviewSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(product=product, user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Товары категории"""
        category = self.get_object()
        products = Product.objects.filter(
            category=category,
            is_available=True
        )

        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductReviewViewSet(viewsets.ModelViewSet):
    """ViewSet для управления отзывами"""
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProductReview.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
