from django.db import models
from apps.products.models import Product, ProductVariant


class Purchase(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Naqd'),
        ('card', 'Karta'),
        ('debt', 'Nasiya'),
        ('transfer', "O'tkazma"),
    ]

    total_uzs = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Jami (UZS)')
    total_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Jami (USD)')
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Jami (eski)')
    payment_method = models.CharField(
        max_length=10, choices=PAYMENT_CHOICES, default='cash', verbose_name="To'lov turi"
    )
    note = models.TextField(blank=True, verbose_name='Izoh')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Harid'
        verbose_name_plural = 'Haridlar'
        ordering = ['-created_at']

    def __str__(self):
        parts = []
        if self.total_uzs:
            parts.append(f"{self.total_uzs:,.0f} UZS")
        if self.total_usd:
            parts.append(f"{self.total_usd:,.2f} USD")
        return f"Harid #{self.id} - {' | '.join(parts) or '0'}"


class PurchaseItem(models.Model):
    CURRENCY_CHOICES = [('uzs', 'UZS'), ('usd', 'USD')]

    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Mahsulot')
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.PROTECT, null=True, blank=True,
        related_name='purchase_items', verbose_name='Variant'
    )
    quantity = models.IntegerField(verbose_name='Miqdor')
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Sotib olish narxi')
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='uzs', verbose_name='Valyuta'
    )

    class Meta:
        verbose_name = 'Harid bandi'
        verbose_name_plural = 'Harid bandlari'

    def __str__(self):
        label = self.product.name
        if self.variant_id:
            label = f"{label} ({self.variant.name})"
        return f"{label} x {self.quantity} ({self.currency.upper()})"

    @property
    def subtotal(self):
        return self.cost_price * self.quantity
