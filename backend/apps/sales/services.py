from django.conf import settings
from django.utils import timezone
from apps.customers.services import send_telegram_message


def _money_parts(sale) -> list[str]:
    parts = []
    if sale.total_uzs:
        parts.append(f"{sale.total_uzs:,.0f} UZS")
    if sale.total_usd:
        parts.append(f"{sale.total_usd:,.2f} USD")
    return parts or ['0']


def _admin_chat_ids() -> list[str]:
    value = str(getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '') or '')
    return [chat_id.strip() for chat_id in value.split(',') if chat_id.strip()]


def _customer_name(sale) -> str:
    return sale.customer.name if sale.customer else "Noma'lum"


def _customer_phone(sale) -> str:
    return sale.customer.phone if sale.customer and sale.customer.phone else "-"


def _debt_due_text(sale, event: str, for_admin: bool = False) -> str:
    due_date = sale.debt_due_date.strftime('%d.%m.%Y')
    total = ' + '.join(_money_parts(sale))

    if event == 'five_days':
        title = "⏰ *Nasiya muddati yaqinlashmoqda*"
        lead = f"To'lov muddatiga 5 kun qoldi: *{due_date}*"
    else:
        title = "🚨 *Nasiya muddati bugun*"
        lead = f"To'lov muddati bugun: *{due_date}*"

    if for_admin:
        return (
            f"{title}\n\n"
            f"🧾 Sotuv: *#{sale.id}*\n"
            f"👤 Mijoz: *{_customer_name(sale)}*\n"
            f"📱 Telefon: {_customer_phone(sale)}\n"
            f"💰 Qarz summasi: *{total}*\n"
            f"📅 {lead}"
        )

    return (
        f"{title}\n\n"
        f"Hurmatli *{_customer_name(sale)}*,\n\n"
        f"🧾 Sotuv: *#{sale.id}*\n"
        f"💰 Qarz summasi: *{total}*\n"
        f"📅 {lead}\n\n"
        f"Iltimos, to'lovni o'z vaqtida amalga oshiring.\n\n"
        f"🎈 BalonCRM"
    )


def send_debt_due_notification(sale, event: str) -> tuple[bool, bool]:
    customer_sent = False
    admin_sent = False

    if sale.customer and sale.customer.is_linked and sale.customer.notifications_enabled:
        customer_sent = send_telegram_message(
            sale.customer.telegram_chat_id,
            _debt_due_text(sale, event, for_admin=False),
        )

    admin_text = _debt_due_text(sale, event, for_admin=True)
    admin_results = [
        send_telegram_message(chat_id, admin_text)
        for chat_id in _admin_chat_ids()
    ]
    admin_sent = any(admin_results)

    return customer_sent, admin_sent


def mark_debt_due_notification_sent(sale, event: str):
    now = timezone.now()
    if event == 'five_days':
        sale.debt_due_5_days_reminded_at = now
        sale.save(update_fields=['debt_due_5_days_reminded_at'])
    elif event == 'today':
        sale.debt_due_today_reminded_at = now
        sale.save(update_fields=['debt_due_today_reminded_at'])
