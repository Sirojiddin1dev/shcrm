from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from .models import Category, Product, ProductVariant
from .serializers import (
    CategorySerializer, ProductSerializer, ProductListSerializer,
    ProductVariantSerializer,
)


def _category_money_total(price_field: str, currency: str):
    """Kategoriyadagi faol variantlar bo'yicha narx × miqdor yig'indisi."""
    money_field = DecimalField(max_digits=20, decimal_places=2)
    return Coalesce(
        Sum(
            ExpressionWrapper(
                F(price_field) * F('products__variants__quantity'),
                output_field=money_field,
            ),
            filter=Q(
                products__is_active=True,
                products__variants__is_active=True,
                products__variants__currency=currency,
            ),
        ),
        Value(0, output_field=money_field),
        output_field=money_field,
    )


@extend_schema(tags=['products'])
@extend_schema_view(
    list=extend_schema(summary='Kategoriyalar ro\'yxati'),
    create=extend_schema(summary='Yangi kategoriya'),
    retrieve=extend_schema(summary='Kategoriya ma\'lumoti'),
    update=extend_schema(summary='Kategoriya tahrirlash'),
    destroy=extend_schema(summary='Kategoriya o\'chirish'),
)
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.annotate(
        product_count=Count(
            'products', filter=Q(products__is_active=True), distinct=True
        ),
        total_quantity=Coalesce(
            Sum(
                'products__variants__quantity',
                filter=Q(
                    products__is_active=True,
                    products__variants__is_active=True,
                ),
            ),
            Value(0),
        ),
        total_sale_price_uzs=_category_money_total('products__variants__sale_price', 'uzs'),
        total_sale_price_usd=_category_money_total('products__variants__sale_price', 'usd'),
        total_cost_price_uzs=_category_money_total('products__variants__cost_price', 'uzs'),
        total_cost_price_usd=_category_money_total('products__variants__cost_price', 'usd'),
    ).order_by('name')
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


@extend_schema(tags=['products'])
@extend_schema_view(
    list=extend_schema(
        summary='Mahsulotlar ro\'yxati',
        description='Filter: `?category=1`, Qidirish: `?search=balon` (nom, variant nomi yoki shtrix-kod bo\'yicha)',
    ),
    create=extend_schema(summary='Yangi mahsulot qo\'shish'),
    retrieve=extend_schema(summary='Mahsulot ma\'lumoti'),
    update=extend_schema(summary='Mahsulot tahrirlash'),
    partial_update=extend_schema(summary='Mahsulot qisman tahrirlash'),
    destroy=extend_schema(summary='Mahsulot o\'chirish (is_active=False)'),
)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = (
        Product.objects.select_related('category')
        .prefetch_related('variants')
        .filter(is_active=True)
        .annotate(variant_count=Count('variants', filter=Q(variants__is_active=True)))
    )
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'variants__name', 'variants__barcode']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer

    @extend_schema(
        summary='Kam qolgan variantlar',
        description='Miqdori `low_stock_threshold` dan kam bo\'lgan variantli mahsulotlar.',
    )
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        products = self.get_queryset().filter(
            variants__is_active=True,
            variants__quantity__lte=F('variants__low_stock_threshold'),
        ).distinct()
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        return Response(status=204)

    @extend_schema(
        summary='Sotuv uchun mahsulotlar',
        description='Faol variantlari bor mahsulotlar (har biri variantlari bilan). Sotuv formasi uchun.',
    )
    @action(detail=False, methods=['get'])
    def for_sale(self, request):
        products = self.get_queryset().filter(variants__is_active=True).distinct()
        data = []
        for p in products:
            variants = [
                {'id': v.id, 'name': v.name,
                 'sale_price': v.sale_price,
                 'cost_price': v.cost_price,
                 'currency': v.currency,
                 'unit': v.unit,
                 'quantity': v.quantity}
                for v in p.variants.all() if v.is_active
            ]
            if not variants:
                continue
            total_qty = sum(v['quantity'] for v in variants)
            data.append({
                'id': p.id, 'name': p.name,
                'quantity': total_qty,
                'has_variants': True,
                'variants': variants,
            })
        return Response(data)


@extend_schema(tags=['products'])
@extend_schema_view(
    list=extend_schema(
        summary='Variantlar ro\'yxati',
        description='Filter: `?product=1`',
    ),
    create=extend_schema(summary='Yangi variant qo\'shish'),
    retrieve=extend_schema(summary='Variant ma\'lumoti'),
    update=extend_schema(summary='Variant tahrirlash'),
    partial_update=extend_schema(summary='Variant qisman tahrirlash'),
    destroy=extend_schema(summary='Variant o\'chirish (is_active=False)'),
)
class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.select_related('product').filter(is_active=True)
    serializer_class = ProductVariantSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['product']
    search_fields = ['name', 'barcode']

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        return Response(status=204)
