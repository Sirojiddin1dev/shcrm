from django.contrib import admin
from .models import Category, Product, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = (
        'name', 'barcode', 'cost_price', 'sale_price',
        'currency', 'quantity', 'unit', 'low_stock_threshold', 'is_active',
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'total_quantity', 'variant_count', 'status', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'variants__name', 'variants__barcode')
    ordering = ('name',)
    inlines = [ProductVariantInline]

    @admin.display(description='Variantlar')
    def variant_count(self, obj):
        return obj.variants.filter(is_active=True).count()


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'product', 'sale_price', 'cost_price',
        'currency', 'quantity', 'unit', 'status', 'is_active',
    )
    list_filter = ('is_active', 'currency', 'product__category')
    search_fields = ('name', 'barcode', 'product__name')
    ordering = ('product__name', 'name')
