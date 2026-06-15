"""
Qarzi bor va botga ulangan mijozlarga avtomatik eslatma yuborish.

Cron orqali ishlatish (har kuni 10:00 da):
    0 10 * * * /var/www/bcrm/backend/venv/bin/python /var/www/bcrm/backend/manage.py send_debt_reminders

Yoki qo'lda:
    python manage.py send_debt_reminders --min-days=3
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.customers.models import Customer
from apps.customers.services import send_debt_reminder


class Command(BaseCommand):
    help = "Qarzdor mijozlarga Telegram orqali eslatma yuboradi"

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-days', type=int, default=3,
            help='Oxirgi eslatmadan kamida shuncha kun o\'tgan bo\'lsa qayta yuborish (default: 3)'
        )
        parser.add_argument(
            '--min-debt', type=int, default=10000,
            help='Minimal qarz (so\'mda). Bundan kam bo\'lsa eslatma yuborilmaydi (default: 10000)'
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Faqat ko\'rsatish, yuborish yo\'q'
        )

    def handle(self, *args, **options):
        min_days = options['min_days']
        min_debt = options['min_debt']
        dry_run = options['dry_run']

        cutoff = timezone.now() - timedelta(days=min_days)

        from django.db.models import Q
        qs = Customer.objects.filter(
            Q(debt_uzs__gte=min_debt) | Q(debt_usd__gt=0),
            notifications_enabled=True,
        ).exclude(telegram_chat_id='')

        qs = qs.filter(Q(last_debt_reminder_at__lte=cutoff) | Q(last_debt_reminder_at__isnull=True))

        total = qs.count()
        self.stdout.write(f"Topildi: {total} ta mijoz")

        sent = 0
        failed = 0
        for customer in qs:
            debt_str = f"{customer.debt_uzs:,.0f} UZS" + (f" + {customer.debt_usd:,.2f} USD" if customer.debt_usd else "")
            self.stdout.write(
                f"  → {customer.name} ({customer.phone}): {debt_str}",
                ending=' '
            )
            if dry_run:
                self.stdout.write(self.style.WARNING('[DRY-RUN]'))
                continue
            if send_debt_reminder(customer):
                sent += 1
                self.stdout.write(self.style.SUCCESS('✓'))
            else:
                failed += 1
                self.stdout.write(self.style.ERROR('✗'))

        self.stdout.write(self.style.SUCCESS(
            f"\nYakun: yuborildi={sent}, xato={failed}, jami={total}"
        ))
