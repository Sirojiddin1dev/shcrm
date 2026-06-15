from django.contrib import admin
from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('cost_price', 'currency')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'total_uzs', 'total_usd', 'payment_method', 'paid_amount', 'remaining_amount', 'debt_due_date', 'is_overdue', 'created_at')
    list_filter = ('payment_method', 'created_at')
    search_fields = ('customer__name',)
    readonly_fields = (
        'is_overdue', 'remaining_amount', 'total',
        'debt_due_5_days_reminded_at', 'debt_due_today_reminded_at',
    )
    fields = (
        'customer', 'total_uzs', 'total_usd', 'discount',
        'payment_method', 'paid_amount', 'remaining_amount',
        'debt_due_date', 'is_overdue',
        'debt_due_5_days_reminded_at', 'debt_due_today_reminded_at',
        'note',
    )
    inlines = [SaleItemInline]
    ordering = ('-created_at',)
