import requests
from django.conf import settings


def _fmt_num(amount, currency: str) -> str:
    """Summani valyutaga mos kasr xonalari bilan formatlash (valyuta belgisisiz)."""
    if (currency or 'uzs').lower() == 'usd':
        return f"{amount:,.2f}"
    return f"{amount:,.0f}"


def _admin_chat_ids() -> list[str]:
    value = str(getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '') or '')
    return [chat_id.strip() for chat_id in value.split(',') if chat_id.strip()]


def send_sale_notification(sale):
    token = settings.TELEGRAM_BOT_TOKEN
    chat_ids = _admin_chat_ids()
    if not token or not chat_ids:
        return

    items_text = '\n'.join(
        f"  • {item.product.name}"
        f"{f' ({item.variant.name})' if item.variant_id else ''}"
        f" — {item.quantity} × {_fmt_num(item.price, item.currency)} = "
        f"{_fmt_num(item.price * item.quantity, item.currency)} {item.currency.upper()}"
        for item in sale.items.all()
    )
    customer_name = sale.customer.name if sale.customer else 'Noma\'lum'
    customer_phone = sale.customer.phone if sale.customer and sale.customer.phone else '-'
    method_map = {'cash': 'Naqd', 'card': 'Karta', 'debt': 'Nasiya', 'transfer': "O'tkazma"}
    payment = method_map.get(sale.payment_method, sale.payment_method)

    total_parts = []
    if sale.total_uzs:
        total_parts.append(f"{sale.total_uzs:,.0f} UZS")
    if sale.total_usd:
        total_parts.append(f"{sale.total_usd:,.2f} USD")
    total_str = ' + '.join(total_parts) or '0'

    text = (
        f"🛒 *Yangi sotuv #{sale.id}*\n"
        f"👤 Mijoz: {customer_name}\n"
        f"📱 Telefon: {customer_phone}\n"
        f"💳 To'lov: {payment}\n\n"
        f"📦 *Mahsulotlar:*\n{items_text}\n\n"
        f"💰 Jami: *{total_str}*"
    )
    if sale.discount:
        text += f"\n🏷 Chegirma: {sale.discount:,.0f} UZS"

    for chat_id in chat_ids:
        try:
            requests.post(
                f'https://api.telegram.org/bot{token}/sendMessage',
                json={'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'},
                timeout=5,
            )
        except Exception:
            pass
