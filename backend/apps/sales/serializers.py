from decimal import Decimal
from rest_framework import serializers
from django.db import transaction
from .models import Sale, SaleItem
from apps.products.models import Product, ProductVariant
from apps.customers.models import Customer


class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True, default='')
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = SaleItem
        fields = (
            'id', 'product', 'product_name', 'variant', 'variant_name',
            'quantity', 'price', 'currency', 'cost_price', 'subtotal',
        )
        read_only_fields = ('id', 'cost_price', 'currency')


class SaleItemCreateSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.filter(is_active=True),
    )
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
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
        if variant.quantity < data['quantity']:
            raise serializers.ValidationError(
                f"{product.name} ({variant.name}) uchun yetarli miqdor yo'q "
                f"(mavjud: {variant.quantity})"
            )

        if not data.get('currency'):
            data['currency'] = variant.currency
        return data


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True, default='')
    profit = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    remaining_amount = serializers.ReadOnlyField()
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Sale
        fields = (
            'id', 'customer', 'customer_name', 'items',
            'total_uzs', 'total_usd', 'discount', 'profit',
            'payment_method', 'payment_method_display',
            'paid_amount', 'remaining_amount',
            'debt_due_date', 'is_overdue',
            'debt_due_5_days_reminded_at', 'debt_due_today_reminded_at',
            'note', 'created_at',
        )
        read_only_fields = (
            'id', 'debt_due_5_days_reminded_at', 'debt_due_today_reminded_at',
            'created_at',
        )


class SaleCreateSerializer(serializers.Serializer):
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        required=False, allow_null=True
    )
    items = SaleItemCreateSerializer(many=True)
    total_uzs = serializers.DecimalField(max_digits=14, decimal_places=2, default=0, min_value=Decimal('0'))
    total_usd = serializers.DecimalField(max_digits=14, decimal_places=2, default=0, min_value=Decimal('0'))
    discount = serializers.DecimalField(max_digits=14, decimal_places=2, default=0, min_value=Decimal('0'))
    payment_method = serializers.ChoiceField(choices=Sale.PAYMENT_CHOICES, default='cash')
    debt_due_date = serializers.DateField(required=False, allow_null=True, default=None)
    note = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, data):
        payment_method = data.get('payment_method')
        if payment_method in ('debt', 'transfer') and not data.get('customer'):
            raise serializers.ValidationError(
                {'customer': "Nasiya yoki o'tkazma sotuvda mijozni tanlash majburiy."}
            )
        if payment_method == 'debt' and not data.get('debt_due_date'):
            raise serializers.ValidationError(
                {'debt_due_date': "Nasiya sotuvda to'lov muddatini kiriting."}
            )
        if payment_method != 'debt':
            data['debt_due_date'] = None
        return data

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Kamida bitta mahsulot kerak")
        return value

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        customer = validated_data.get('customer')

        for item in items_data:
            if not item.get('currency'):
                item['currency'] = item['variant'].currency

        # Frontend yuborgan total_uzs/total_usd ni ishlatamiz
        # Agar 0 bo'lsa yoki yuborilmasa — itemlardan hisoblaymiz
        total_uzs = validated_data.pop('total_uzs', Decimal('0'))
        total_usd = validated_data.pop('total_usd', Decimal('0'))

        if not total_uzs:
            total_uzs = sum(
                item['price'] * item['quantity']
                for item in items_data if item['currency'] == 'uzs'
            ) or Decimal('0')
            discount = validated_data.get('discount', Decimal('0'))
            total_uzs = max(total_uzs - discount, Decimal('0'))

        if not total_usd:
            total_usd = sum(
                item['price'] * item['quantity']
                for item in items_data if item['currency'] == 'usd'
            ) or Decimal('0')

        sale = Sale.objects.create(
            total_uzs=total_uzs,
            total_usd=total_usd,
            total=total_uzs,
            **validated_data,
        )

        for item_data in items_data:
            product = item_data['product']
            variant = item_data['variant']
            SaleItem.objects.create(
                sale=sale,
                product=product,
                variant=variant,
                quantity=item_data['quantity'],
                price=item_data['price'],
                currency=item_data['currency'],
                cost_price=variant.cost_price,
            )
            variant.quantity -= item_data['quantity']
            variant.save(update_fields=['quantity', 'updated_at'])

        if customer:
            if validated_data.get('payment_method') == 'debt':
                customer.debt_uzs += total_uzs
                customer.debt_usd += total_usd
            customer.total_spent_uzs += total_uzs
            customer.total_spent_usd += total_usd
            customer.update_status()
            customer.save()

        return sale


class SaleListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True, default='')
    item_count = serializers.IntegerField(source='items.count', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    remaining_amount = serializers.ReadOnlyField()

    class Meta:
        model = Sale
        fields = (
            'id', 'customer_name', 'total_uzs', 'total_usd', 'discount',
            'payment_method_display', 'item_count',
            'paid_amount', 'remaining_amount',
            'debt_due_date', 'is_overdue',
            'debt_due_5_days_reminded_at', 'debt_due_today_reminded_at',
            'created_at',
        )
