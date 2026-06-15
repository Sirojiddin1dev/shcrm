from decimal import Decimal
from rest_framework import serializers
from django.db import transaction
from .models import Purchase, PurchaseItem
from apps.products.models import Product, ProductVariant


class PurchaseItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True, default='')
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = PurchaseItem
        fields = (
            'id', 'product', 'product_name', 'variant', 'variant_name',
            'quantity', 'cost_price', 'currency', 'subtotal',
        )
        read_only_fields = ('id', 'currency')


class PurchaseItemCreateSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.filter(is_active=True),
    )
    quantity = serializers.IntegerField(min_value=1)
    cost_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    currency = serializers.ChoiceField(
        choices=[('uzs', 'UZS'), ('usd', 'USD')],
        required=False, default=None,
    )

    def validate(self, data):
        product = data['product']
        variant = data['variant']
        if variant.product_id != product.id:
            raise serializers.ValidationError(
                f"{variant.name} varianti {product.name} mahsulotiga tegishli emas."
            )
        return data


class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True, read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Purchase
        fields = (
            'id', 'items',
            'total_uzs', 'total_usd',
            'payment_method', 'payment_method_display',
            'note', 'created_at',
        )
        read_only_fields = ('id', 'total_uzs', 'total_usd', 'created_at')


class PurchaseCreateSerializer(serializers.Serializer):
    items = PurchaseItemCreateSerializer(many=True)
    total_uzs = serializers.DecimalField(max_digits=14, decimal_places=2, default=0, min_value=Decimal('0'))
    total_usd = serializers.DecimalField(max_digits=14, decimal_places=2, default=0, min_value=Decimal('0'))
    payment_method = serializers.ChoiceField(choices=Purchase.PAYMENT_CHOICES, default='cash')
    note = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Kamida bitta mahsulot kerak")
        return value

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        frontend_uzs = validated_data.pop('total_uzs', Decimal('0'))
        frontend_usd = validated_data.pop('total_usd', Decimal('0'))

        # Har bir item uchun currency: frontend yuborsa shu, yubormasа variantdan
        for item in items_data:
            if not item.get('currency'):
                item['currency'] = item['variant'].currency

        # total_uzs va total_usd alohida
        calc_uzs = sum(
            item['cost_price'] * item['quantity']
            for item in items_data if item['currency'] == 'uzs'
        ) or Decimal('0')
        calc_usd = sum(
            item['cost_price'] * item['quantity']
            for item in items_data if item['currency'] == 'usd'
        ) or Decimal('0')

        # Frontend yuborgan qiymatni ishlatamiz, 0 bo'lsa hisoblaymiz
        total_uzs = frontend_uzs if frontend_uzs else calc_uzs
        total_usd = frontend_usd if frontend_usd else calc_usd

        purchase = Purchase.objects.create(
            total_uzs=total_uzs,
            total_usd=total_usd,
            total=total_uzs,
            **validated_data,
        )

        for item_data in items_data:
            product = item_data['product']
            variant = item_data['variant']
            PurchaseItem.objects.create(
                purchase=purchase,
                product=product,
                variant=variant,
                quantity=item_data['quantity'],
                cost_price=item_data['cost_price'],
                currency=item_data['currency'],
            )
            # Variant qoldig'ini oshiramiz va tan narxini yangilaymiz
            variant.quantity += item_data['quantity']
            variant.cost_price = item_data['cost_price']
            variant.save(update_fields=['quantity', 'cost_price', 'updated_at'])

        return purchase


class PurchaseListSerializer(serializers.ModelSerializer):
    item_count = serializers.IntegerField(source='items.count', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Purchase
        fields = (
            'id', 'total_uzs', 'total_usd',
            'payment_method_display', 'item_count',
            'note', 'created_at',
        )
