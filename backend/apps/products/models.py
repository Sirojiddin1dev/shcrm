from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nomi')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Kategoriya'
        verbose_name_plural = 'Kategoriyalar'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Mahsulot — faqat tavsifiy ma'lumot. Narx, valyuta, miqdor, birlik
    kabi tijoriy maydonlar variantlarda (ProductVariant) saqlanadi."""

    name = models.CharField(max_length=200, verbose_name='Nomi')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products', verbose_name='Kategoriya'
    )
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name='Rasm')
    description = models.TextField(blank=True, verbose_name='Tavsif')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mahsulot'
        verbose_name_plural = 'Mahsulotlar'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def active_variants(self):
        return self.variants.filter(is_active=True)

    @property
    def has_variants(self) -> bool:
        return self.active_variants.exists()

    @property
    def total_quantity(self) -> int:
        """Mahsulotning umumiy qoldig'i = faol variantlar miqdori yig'indisi."""
        from django.db.models import Sum
        return self.active_variants.aggregate(t=Sum('quantity'))['t'] or 0

    @property
    def status(self):
        """Eng kam qolgan variant holatiga qarab umumiy holat."""
        statuses = [v.status for v in self.active_variants]
        if not statuses:
            return 'critical'
        if 'critical' in statuses:
            return 'critical'
        if 'low' in statuses:
            return 'low'
        return 'good'


class ProductVariant(models.Model):
    """Mahsulot varianti — narx, valyuta, miqdor, birlik shu yerda.

    Har bir mahsulot kamida bitta variant bilan ifodalanadi. Oddiy (bir xil)
    mahsulot — bitta 'Asosiy' variantli mahsulotdir.
    """
    UNIT_CHOICES = [
        ('dona', 'Dona'),
        ('kg', 'Kg'),
        ('litr', 'Litr'),
        ('metr', 'Metr'),
    ]

    CURRENCY_CHOICES = [
        ('uzs', 'UZS'),
        ('usd', 'USD'),
    ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='variants',
        verbose_name='Mahsulot'
    )
    name = models.CharField(max_length=150, verbose_name='Variant nomi')
    barcode = models.CharField(max_length=50, blank=True, verbose_name='Shtrix kod')
    cost_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Sotib olish narxi'
    )
    sale_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Sotish narxi'
    )
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='uzs',
        verbose_name='Valyuta'
    )
    quantity = models.IntegerField(default=0, verbose_name='Miqdor')
    unit = models.CharField(
        max_length=10, choices=UNIT_CHOICES, default='dona', verbose_name='Birlik'
    )
    low_stock_threshold = models.IntegerField(default=5, verbose_name='Kam qolish chegarasi')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Variant'
        verbose_name_plural = 'Variantlar'
        ordering = ['name']

    def __str__(self):
        return f"{self.product.name} — {self.name}"

    @property
    def status(self):
        if self.quantity <= 0:
            return 'critical'
        if self.quantity <= self.low_stock_threshold:
            return 'low'
        return 'good'
