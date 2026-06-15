"""
Nasiya sotuv muddati yaqinlashganda Telegram xabar yuborish.

Cron orqali har kuni ishga tushirish:
    0 9 * * * /var/www/bcrm/backend/venv/bin/python /var/www/bcrm/backend/manage.py send_debt_due_notifications

Qo'lda tekshirish:
    python manage.py send_debt_due_notifications --dry-run
"""
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from apps.sales.models import Sale
from apps.sales.services import (
    mark_debt_due_notification_sent,
    send_debt_due_notification,
)


class Command(BaseCommand):
    help = "Nasiya muddati 5 kun qolganda va bugun kelganda mijoz/adminlarga Telegram xabar yuboradi"

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-before',
            type=int,
            default=5,
            help='Muddatdan necha kun oldin eslatish (default: 5)',
        )
        parser.add_argument(
            '--date',
            help='Bugungi sana o\'rniga shu sanani ishlatish (YYYY-MM-DD)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Faqat topilgan sotuvlarni ko\'rsatish, xabar yubormaslik',
        )

    def handle(self, *args, **options):
        days_before = options['days_before']
        dry_run = options['dry_run']
        today = self._get_today(options.get('date'))
        before_date = today + timedelta(days=days_before)

        base_qs = (
            Sale.objects.select_related('customer')
            .filter(payment_method='debt', debt_due_date__isnull=False)
            .filter(Q(total_uzs__gt=0) | Q(total_usd__gt=0))
            .filter(Q(customer__debt_uzs__gt=0) | Q(customer__debt_usd__gt=0))
        )

        jobs = [
            (
                'five_days',
                before_date,
                base_qs.filter(
                    debt_due_date=before_date,
                    debt_due_5_days_reminded_at__isnull=True,
                ),
            ),
            (
                'today',
                today,
                base_qs.filter(
                    debt_due_date=today,
                    debt_due_today_reminded_at__isnull=True,
                ),
            ),
        ]

        total_sent = 0
        total_failed = 0

        for event, due_date, queryset in jobs:
            label = '5 kun oldin' if event == 'five_days' else 'muddat kuni'
            count = queryset.count()
            self.stdout.write(f"{label} ({due_date}): {count} ta sotuv")

            for sale in queryset:
                customer = sale.customer
                customer_name = customer.name if customer else "Noma'lum"
                amount = self._amount_text(sale)
                self.stdout.write(
                    f"  -> #{sale.id} {customer_name}: {amount}",
                    ending=' ',
                )

                if dry_run:
                    self.stdout.write(self.style.WARNING('[DRY-RUN]'))
                    continue

                customer_sent, admin_sent = send_debt_due_notification(sale, event)
                if customer_sent or admin_sent:
                    mark_debt_due_notification_sent(sale, event)
                    total_sent += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ mijoz={'ha' if customer_sent else 'yoq'}, "
                            f"admin={'ha' if admin_sent else 'yoq'}"
                        )
                    )
                else:
                    total_failed += 1
                    self.stdout.write(self.style.ERROR('✗ yuborilmadi'))

        self.stdout.write(self.style.SUCCESS(
            f"\nYakun: yuborildi={total_sent}, xato={total_failed}"
        ))

    def _get_today(self, value):
        if value:
            return datetime.strptime(value, '%Y-%m-%d').date()
        return timezone.localdate()

    def _amount_text(self, sale):
        parts = []
        if sale.total_uzs:
            parts.append(f"{sale.total_uzs:,.0f} UZS")
        if sale.total_usd:
            parts.append(f"{sale.total_usd:,.2f} USD")
        return ' + '.join(parts) or '0'
