import secrets
from django.db import models


def _generate_link_token() -> str:
    return secrets.token_urlsafe(16)


class Customer(models.Model):
    STATUS_CHOICES = [
        ('active', 'Faol'),
        ('vip', 'VIP'),
        ('debtor', 'Qarzdor'),
        ('inactive', 'Nofaol'),
    ]

    name = models.CharField(max_length=200, verbose_name='Ism familiya')
    phone = models.CharField(max_length=20, blank=True, db_index=True, verbose_name='Telefon')
    address = models.CharField(max_length=300, blank=True, verbose_name='Manzil')

    debt_uzs = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Qarz (UZS)')
    debt_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Qarz (USD)')

    total_spent_uzs = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Jami xarid (UZS)')
    total_spent_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Jami xarid (USD)')

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name='Status')
    telegram_chat_id = models.CharField(
        max_length=50, blank=True, db_index=True, verbose_name='Telegram chat ID'
    )
    telegram_verified_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Telegram tasdiqlangan vaqti'
    )
    link_token = models.CharField(
        max_length=32, unique=True, default=_generate_link_token,
        verbose_name='Deep link token',
        help_text="Bot deep link: https://t.me/<bot>?start=cust_<token>"
    )
    notifications_enabled = models.BooleanField(default=True, verbose_name='Xabarlar yoqilgan')
    last_debt_reminder_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Oxirgi qarz eslatma vaqti'
    )
    note = models.TextField(blank=True, verbose_name='Izoh')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mijoz'
        verbose_name_plural = 'Mijozlar'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def update_status(self):
        if self.debt_uzs > 0 or self.debt_usd > 0:
            self.status = 'debtor'
        elif self.total_spent_uzs >= 1_000_000:
            self.status = 'vip'
        else:
            self.status = 'active'

    def save(self, *args, **kwargs):
        # Qarz 0 bo'lsa 'debtor' statusni avtomatik tuzatish
        if self.status == 'debtor' and self.debt_uzs <= 0 and self.debt_usd <= 0:
            self.update_status()
        super().save(*args, **kwargs)

    @property
    def is_linked(self) -> bool:
        return bool(self.telegram_chat_id)

    @property
    def is_telegram_verified(self) -> bool:
        return bool(self.telegram_chat_id and self.telegram_verified_at)

    def bot_deep_link(self, bot_username: str) -> str:
        return f"https://t.me/{bot_username}?start=cust_{self.link_token}"

    def normalize_phone(self) -> str:
        return ''.join(c for c in (self.phone or '') if c.isdigit())
