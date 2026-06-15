from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🛒 Yangi sotuv"),
        KeyboardButton(text="📦 Yangi harid"),
    )
    builder.row(
        KeyboardButton(text="👥 Mijozlar"),
        KeyboardButton(text="💰 Qarzdorlar"),
    )
    builder.row(
        KeyboardButton(text="📋 Mahsulotlar"),
        KeyboardButton(text="📈 Oylik hisobot"),
    )
    return builder.as_markup(resize_keyboard=True)


def products_keyboard(products: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        if p.get('has_variants'):
            text = f"{p['name']} ▸ variantlar ({p['quantity']} dona)"
        else:
            text = f"{p['name']} ({p['quantity']} dona) - {float(p['sale_price']):,.0f} so'm"
        builder.button(text=text, callback_data=f"product_{p['id']}")
    builder.button(text="✅ Yakunlash", callback_data="sale_finish")
    builder.button(text="❌ Bekor qilish", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def variants_keyboard(variants: list, mode: str = "sale") -> InlineKeyboardMarkup:
    """Variant tanlash. mode='sale' narx bilan, 'purchase' qoldiq bilan."""
    builder = InlineKeyboardBuilder()
    for v in variants:
        if mode == "sale":
            text = f"{v['name']} ({v['quantity']} dona) - {float(v['sale_price']):,.0f} so'm"
        else:
            text = f"{v['name']} (mavjud: {v['quantity']} dona)"
        builder.button(text=text, callback_data=f"variant_{v['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="variant_back")
    builder.button(text="❌ Bekor qilish", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def customers_keyboard(customers: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Noma'lum mijoz", callback_data="customer_none")
    for c in customers[:15]:
        builder.button(
            text=f"{c['name']} ({c.get('phone', '')})",
            callback_data=f"customer_{c['id']}"
        )
    builder.adjust(1)
    return builder.as_markup()


def payment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💵 Naqd", callback_data="pay_cash")
    builder.button(text="💳 Karta", callback_data="pay_card")
    builder.button(text="📝 Nasiya", callback_data="pay_debt")
    builder.button(text="🏦 O'tkazma", callback_data="pay_transfer")
    builder.adjust(2)
    return builder.as_markup()



def purchase_products_keyboard(products: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        if p.get('has_variants'):
            text = f"{p['name']} ▸ variantlar"
        else:
            text = f"{p['name']} - tan narx: {float(p.get('cost_price', 0)):,.0f} so'm"
        builder.button(text=text, callback_data=f"buy_product_{p['id']}")
    builder.button(text="✅ Yakunlash", callback_data="purchase_finish")
    builder.button(text="❌ Bekor qilish", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data="confirm")
    builder.button(text="❌ Bekor qilish", callback_data="cancel")
    return builder.as_markup()
