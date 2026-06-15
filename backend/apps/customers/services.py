"""
Mijozlarga Telegram bot orqali xabar yuborish servisi.

Sotuv cheki, qarz eslatmasi, to'lov tasdig'i kabi xabarlar shu yerdan yuboriladi.
"""
import logging
from decimal import Decimal
from typing import Optional
import requests
from django.conf import settings
from django.utils import timezone
from .models import Customer

logger = logging.getLogger(__name__)


def _bot_token() -> str:
    return settings.TELEGRAM_BOT_TOKEN


def _fmt_num(amount, currency: str) -> str:
    """Summani valyutaga mos kasr xonalari bilan formatlash (valyuta belgisisiz)."""
    if (currency or 'uzs').lower() == 'usd':
        return f"{amount:,.2f}"
    return f"{amount:,.0f}"


def send_telegram_message(chat_id: str | int, text: str, parse_mode: str = 'Markdown') -> bool:
    """Telegramga xabar yuborish. Xato bo'lsa logga yozadi, False qaytaradi."""
    token = _bot_token()
    if not token or not chat_id:
        logger.warning("Telegram token yoki chat_id yo'q")
        return False
    try:
        resp = requests.post(
            f'https://api.telegram.org/bot{token}/sendMessage',
            json={
                'chat_id': str(chat_id),
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True,
            },
            timeout=8,
        )
        if resp.status_code != 200:
            logger.warning("Telegram xato: %s %s", resp.status_code, resp.text[:200])
            return False
        return True
    except requests.RequestException as exc:
        logger.warning("Telegram so'rovida xato: %s", exc)
        return False


def send_sale_receipt(sale) -> bool:
    """Sotuv yakunlanganda mijozga chek yuborish."""
    customer = sale.customer
    if not customer or not customer.is_linked or not customer.notifications_enabled:
        return False

    items_text = '\n'.join(
        f"  • {item.product.name}"
        f"{f' ({item.variant.name})' if item.variant_id else ''}"
        f" — {item.quantity} × {_fmt_num(item.price, item.currency)} = "
        f"{_fmt_num(item.price * item.quantity, item.currency)} {item.currency.upper()}"
        for item in sale.items.all()
    )
    method_map = {'cash': '💵 Naqd', 'card': '💳 Karta',
                  'debt': '📝 Nasiya', 'transfer': '🏦 Oʻtkazma'}
    payment = method_map.get(sale.payment_method, sale.payment_method)

    total_parts = []
    if sale.total_uzs:
        total_parts.append(f"{sale.total_uzs:,.0f} UZS")
    if sale.total_usd:
        total_parts.append(f"{sale.total_usd:,.2f} USD")
    total_str = ' + '.join(total_parts) or '0'

    text = (
        f"🧾 *Sotuv cheki #{sale.id}*\n"
        f"📅 Sana: {timezone.localtime(sale.created_at).strftime('%d.%m.%Y %H:%M')}\n\n"
        f"📦 *Mahsulotlar:*\n{items_text}\n\n"
        f"💰 *Jami: {total_str}*\n"
        f"{payment}\n"
    )
    if sale.discount and sale.discount > 0:
        text += f"🏷 Chegirma: {sale.discount:,.0f} UZS\n"

    if sale.payment_method == 'debt':
        debt_parts = []
        if customer.debt_uzs > 0:
            debt_parts.append(f"{customer.debt_uzs:,.0f} UZS")
        if customer.debt_usd > 0:
            debt_parts.append(f"{customer.debt_usd:,.2f} USD")
        if debt_parts:
            text += f"\n📝 Qarz sifatida yozildi. Jami qarz: *{' + '.join(debt_parts)}*"
    elif customer.debt_uzs > 0 or customer.debt_usd > 0:
        debt_parts = []
        if customer.debt_uzs > 0:
            debt_parts.append(f"{customer.debt_uzs:,.0f} UZS")
        if customer.debt_usd > 0:
            debt_parts.append(f"{customer.debt_usd:,.2f} USD")
        text += f"\n📝 Joriy qarzingiz: {' + '.join(debt_parts)}"

    text += "\n\n🎈 BalonCRM — xaridingiz uchun rahmat!"
    return send_telegram_message(customer.telegram_chat_id, text)


def send_payment_received(
    customer: Customer,
    amount_uzs: Decimal, amount_usd: Decimal,
    remaining_uzs: Decimal, remaining_usd: Decimal,
) -> bool:
    """Mijoz qarzni to'laganda tasdiq xabari."""
    if not customer.is_linked or not customer.notifications_enabled:
        return False

    paid_parts = []
    if amount_uzs > 0:
        paid_parts.append(f"{amount_uzs:,.0f} UZS")
    if amount_usd > 0:
        paid_parts.append(f"{amount_usd:,.2f} USD")
    paid_str = ' + '.join(paid_parts) or '0'

    text = (
        f"✅ *To'lov qabul qilindi*\n\n"
        f"💰 Miqdor: *{paid_str}*\n"
        f"📅 Sana: {timezone.localtime(timezone.now()).strftime('%d.%m.%Y %H:%M')}\n\n"
    )
    if remaining_uzs > 0 or remaining_usd > 0:
        rem_parts = []
        if remaining_uzs > 0:
            rem_parts.append(f"{remaining_uzs:,.0f} UZS")
        if remaining_usd > 0:
            rem_parts.append(f"{remaining_usd:,.2f} USD")
        text += f"📝 Qolgan qarz: *{' + '.join(rem_parts)}*"
    else:
        text += "🎉 Qarzingiz to'liq yopildi!"
    text += "\n\n🎈 BalonCRM"
    return send_telegram_message(customer.telegram_chat_id, text)


def send_debt_reminder(customer: Customer) -> bool:
    """Qarzi bor mijozga eslatma yuborish."""
    if not customer.is_linked or not customer.notifications_enabled:
        return False
    if customer.debt_uzs <= 0 and customer.debt_usd <= 0:
        return False

    debt_parts = []
    if customer.debt_uzs > 0:
        debt_parts.append(f"*{customer.debt_uzs:,.0f} UZS*")
    if customer.debt_usd > 0:
        debt_parts.append(f"*{customer.debt_usd:,.2f} USD*")

    text = (
        f"⏰ *Qarz eslatmasi*\n\n"
        f"Hurmatli *{customer.name}*,\n\n"
        f"Sizning hozirgi qarzingiz: {' + '.join(debt_parts)}\n\n"
        f"Iltimos, qulay vaqtda to'lab qo'yishingizni so'raymiz. 🙏\n\n"
        f"🎈 BalonCRM"
    )
    sent = send_telegram_message(customer.telegram_chat_id, text)
    if sent:
        customer.last_debt_reminder_at = timezone.now()
        customer.save(update_fields=['last_debt_reminder_at'])
    return sent


def send_link_invitation(customer: Customer, bot_username: str) -> bool:
    """Mijozga botga ulanish linkini yuborish (admin tomonidan boshqa kanalda jo'natiladi)."""
    deep_link = customer.bot_deep_link(bot_username)
    text = (
        f"Hurmatli *{customer.name}*,\n\n"
        f"BalonCRM Telegram botiga ulanish uchun quyidagi tugmani bosing — "
        f"endi barcha sotuv cheklari va qarz eslatmalarini Telegramda olasiz.\n\n"
        f"🔗 [Botga ulanish]({deep_link})\n\n"
        f"🎈 BalonCRM"
    )
    if customer.is_linked:
        return send_telegram_message(customer.telegram_chat_id, text)
    return False


def find_customer_by_phone(phone: str) -> Optional[Customer]:
    """Telefon raqami orqali mijozni topish (raqamlarni solishtiradi)."""
    normalized = ''.join(c for c in phone if c.isdigit())
    if not normalized:
        return None
    for c in Customer.objects.exclude(phone=''):
        if c.normalize_phone() == normalized:
            return c
        # +998 prefiks bo'lmasa qo'shib ko'rish
        if len(normalized) == 9 and c.normalize_phone() == '998' + normalized:
            return c
        if len(c.normalize_phone()) == 9 and ('998' + c.normalize_phone()) == normalized:
            return c
    return None
