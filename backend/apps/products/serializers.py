from decimal import Decimal
from rest_framework import serializers
from .models import Category, Product, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True, default=0)
    total_quantity = serializers.IntegerField(read_only=True, default=0)
    total_sale_price_uzs = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True, default=Decimal('0.00')
    )
    total_sale_price_usd = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True, default=Decimal('0.00')
    )
    total_cost_price_uzs = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True, default=Decimal('0.00')
    )
    total_cost_price_usd = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True, default=Decimal('0.00')
    )

    class Meta:
        model = Category
        fields = (
            'id', 'name', 'product_count', 'total_quantity',
            'total_sale_price_uzs', 'total_sale_price_usd',
            'total_cost_price_uzs', 'total_cost_price_usd',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')


class ProductVariantSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    product_name = serializers.CharField(source='product.name', read_only=True)
    status = serializers.ReadOnlyField()

    class Meta:
        model = ProductVariant
        fields = (
            'id', 'product', 'product_name', 'name', 'barcode',
            'cost_price', 'sale_price', 'currency', 'quantity', 'unit',
            'low_stock_threshold', 'is_active', 'status',
            'created_at', 'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')
        extra_kwargs = {
            # Product nested-da kelganda majburiy emas — parent o'rnatadi
            'product': {'required': False},
        }

    def validate(self, data):
        # Alohida (nested emas) variant yaratishda product majburiy
        if self.parent is None and not self.instance and not data.get('product'):
            raise serializers.ValidationError({'product': 'Mahsulot tanlanishi shart.'})
        return data


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    status = serializers.ReadOnlyField()
    variants = ProductVariantSerializer(many=True)
    has_variants = serializers.ReadOnlyField()
    total_quantity = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'category', 'category_name',
            'image', 'description', 'is_active',
            'status', 'has_variants', 'total_quantity', 'variants',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_variants(self, value):
        # Yaratishda kamida bitta variant majburiy
        if self.instance is None and not value:
            raise serializers.ValidationError('Kamida bitta variant qo\'shing.')
        return value

    def create(self, validated_data):
        variants_data = validated_data.pop('variants', [])
        product = super().create(validated_data)
        for v in variants_data:
            v.pop('id', None)
            v.pop('product', None)
            ProductVariant.objects.create(product=product, **v)
        return product

    def update(self, instance, validated_data):
        variants_data = validated_data.pop('variants', None)
        product = super().update(instance, validated_data)
        if variants_data is not None:
            self._sync_variants(product, variants_data)
        return product

    def _sync_variants(self, product, variants_data):
        """Yuborilgan variantlar bilan sinxron: yangi qo'shadi, mavjudni yangilaydi,
        ro'yxatda yo'qlarini faolsizlantiradi."""
        existing = {v.id: v for v in product.variants.all()}
        sent_ids = set()
        for v in variants_data:
            v.pop('product', None)
            vid = v.pop('id', None)
            if vid and vid in existing:
                variant = existing[vid]
                for attr, val in v.items():
                    setattr(variant, attr, val)
                variant.save()
                sent_ids.add(vid)
            else:
                ProductVariant.objects.create(product=product, **v)
        # Yuborilmagan variantlarni faolsizlantirish (o'chirish o'rniga — tarix saqlanadi)
        for vid, variant in existing.items():
            if vid not in sent_ids and variant.is_active:
                variant.is_active = False
                variant.save(update_fields=['is_active'])


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    status = serializers.ReadOnlyField()
    has_variants = serializers.ReadOnlyField()
    total_quantity = serializers.ReadOnlyField()
    variant_count = serializers.IntegerField(read_only=True, default=0)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'category_name', 'status',
            'has_variants', 'total_quantity', 'variant_count', 'variants',
        )
