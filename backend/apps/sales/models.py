from django.db import models
from apps.products.models import Product, ProductVariant
from apps.customers.models import Customer


class Sale(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Naqd'),
        ('card', 'Karta'),
        ('debt', 'Nasiya'),
        ('transfer', "O'tkazma"),
    ]

    CURRENCY_CHOICES = [('uzs', 'UZS'), ('usd', 'USD')]

    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sales', verbose_name='Mijoz'
    )
    # Alohida valyuta bo'yicha jami (aralash sotuvlarda ikkalasi ham to'ldiriladi)
    total_uzs = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name='Jami (UZS)'
    )
    total_usd = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name='Jami (USD)'
    )
    # Eski total — backward compat uchun (total_uzs bilan teng)
    total = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name='Jami (UZS, eski)'
    )
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Chegirma')
    payment_method = models.CharField(
        max_length=10, choices=PAYMENT_CHOICES, default='cash', verbose_name="To'lov turi"
    )
    paid_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="To'langan summa",
        help_text="Nasiya sotuvda mijoz to'lagan miqdor"
    )
    note = models.TextField(blank=True, verbose_name='Izoh')
    debt_due_date = models.DateField(
        null=True, blank=True, verbose_name='Nasiya muddati',
        help_text="Faqat nasiya sotuvlar uchun: to'lov muddati"
    )
    debt_due_5_days_reminded_at = models.DateTimeField(
        null=True, blank=True, verbose_name='5 kun oldin eslatma yuborilgan vaqt'
    )
    debt_due_today_reminded_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Muddat kuni eslatma yuborilgan vaqt'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sotuv'
        verbose_name_plural = 'Sotuvlar'
        ordering = ['-created_at']

    def __str__(self):
        parts = []
        if self.total_uzs:
            parts.append(f"{self.total_uzs:,.0f} UZS")
        if self.total_usd:
            parts.append(f"{self.total_usd:,.2f} USD")
        return f"Sotuv #{self.id} - {' | '.join(parts) or '0'}"

    @property
    def remaining_amount(self):
        """UZS bo'yicha qolgan qarz (paid_amount UZS da hisoblanadi)."""
        return max(self.total_uzs - self.paid_amount, 0)

    @property
    def is_overdue(self) -> bool:
        if self.payment_method != 'debt' or not self.debt_due_date:
            return False
        from django.utils.timezone import now
        return self.debt_due_date < now().date()

    @property
    def cost_total(self):
        return sum(item.cost_price * item.quantity for item in self.items.all())

    @property
    def profit(self):
        return self.total_uzs - self.cost_total


class SaleItem(models.Model):
    CURRENCY_CHOICES = [('uzs', 'UZS'), ('usd', 'USD')]

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Mahsulot')
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.PROTECT, null=True, blank=True,
        related_name='sale_items', verbose_name='Variant'
    )
    quantity = models.IntegerField(verbose_name='Miqdor')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Narxi')
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='uzs', verbose_name='Valyuta'
    )
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Tan narx')

    class Meta:
        verbose_name = 'Sotuv bandi'
        verbose_name_plural = 'Sotuv bandlari'

    def __str__(self):
        label = self.product.name
        if self.variant_id:
            label = f"{label} ({self.variant.name})"
        return f"{label} x {self.quantity} ({self.currency.upper()})"

    @property
    def subtotal(self):
        return self.price * self.quantity
