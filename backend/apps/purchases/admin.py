from django.contrib import admin
from .models import Purchase, PurchaseItem


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_uzs', 'total_usd', 'payment_method', 'note', 'created_at')
    list_filter = ('payment_method', 'created_at')
    search_fields = ('note',)
    inlines = [PurchaseItemInline]
    ordering = ('-created_at',)
