from decimal import Decimal
from rest_framework import serializers
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_linked = serializers.ReadOnlyField()
    is_telegram_verified = serializers.ReadOnlyField()

    class Meta:
        model = Customer
        fields = (
            'id', 'name', 'phone', 'address',
            'debt_uzs', 'debt_usd',
            'total_spent_uzs', 'total_spent_usd',
            'status', 'status_display',
            'telegram_chat_id', 'is_linked', 'is_telegram_verified',
            'telegram_verified_at', 'link_token',
            'notifications_enabled', 'last_debt_reminder_at',
            'note', 'created_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'total_spent_uzs', 'total_spent_usd',
            'telegram_verified_at', 'link_token', 'last_debt_reminder_at',
            'created_at', 'updated_at',
        )


class CustomerListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_linked = serializers.ReadOnlyField()
    is_telegram_verified = serializers.ReadOnlyField()

    class Meta:
        model = Customer
        fields = (
            'id', 'name', 'phone',
            'debt_uzs', 'debt_usd',
            'total_spent_uzs', 'total_spent_usd',
            'status', 'status_display', 'is_linked',
            'is_telegram_verified', 'telegram_verified_at',
        )


class LinkByPhoneSerializer(serializers.Serializer):
    phone = serializers.CharField()
    chat_id = serializers.CharField()
    full_name = serializers.CharField(required=False, allow_blank=True)


class LinkByTokenSerializer(serializers.Serializer):
    token = serializers.CharField()
    chat_id = serializers.CharField()
    full_name = serializers.CharField(required=False, allow_blank=True)


class PaymentSerializer(serializers.Serializer):
    amount_uzs = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal('0'), default=Decimal('0')
    )
    amount_usd = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal('0'), default=Decimal('0')
    )
    note = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, data):
        if not data.get('amount_uzs') and not data.get('amount_usd'):
            raise serializers.ValidationError(
                "Kamida bitta to'lov summasini kiriting (amount_uzs yoki amount_usd)"
            )
        return data
