import requests
from django.conf import settings


def send_purchase_notification(purchase):
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
    if not token or not chat_id:
        return

    items_text = '\n'.join(
        f"  • {item.product.name}"
        f"{f' ({item.variant.name})' if item.variant_id else ''}"
        f" x{item.quantity} = {item.cost_price * item.quantity:,.0f} so'm"
        f" ({item.cost_price:,.0f} so'm/dona)"
        for item in purchase.items.all()
    )
    method_map = {'cash': 'Naqd', 'card': 'Karta', 'debt': 'Nasiya', 'transfer': "O'tkazma"}
    payment = method_map.get(purchase.payment_method, purchase.payment_method)

    text = (
        f"📦 *Yangi harid #{purchase.id}*\n"
        f"💳 To'lov: {payment}\n"
        f"📋 Mahsulotlar:\n{items_text}\n"
        f"💰 Jami: *{purchase.total:,.0f} so'm*"
    )
    if purchase.note:
        text += f"\n📝 Izoh: {purchase.note}"

    try:
        requests.post(
            f'https://api.telegram.org/bot{token}/sendMessage',
            json={'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'},
            timeout=5,
        )
    except Exception:
        pass
