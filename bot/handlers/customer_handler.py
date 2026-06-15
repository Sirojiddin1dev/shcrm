"""
Mijozlar (customer) uchun bot handlerlari.

Ulanish usullari:
  1. /start cust_<token>  — admin yuborgan deep link
  2. Contact share        — telefon raqam orqali

Mijoz menyusi:
  💳 Qarzlarim       — joriy qarz holati
  🧾 Sotuv tarixi    — oxirgi 10 ta sotuv
  📞 Admin           — +998 91 767 66 66
"""
from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import (
    Message, KeyboardButton, ReplyKeyboardMarkup,
    ReplyKeyboardRemove, InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import api_client
from config import ADMIN_CHAT_IDS
from keyboards import main_menu
import user_manager

router = Router()

ADMIN_PHONE = "+998917676666"
ADMIN_PHONE_DISPLAY = "+998 91 767 66 66"


def _debt_line(customer: dict) -> str:
    """Mijoz qarzini bir qatorli matn sifatida qaytaradi."""
    uzs = float(customer.get('debt_uzs', 0))
    usd = float(customer.get('debt_usd', 0))
    parts = []
    if uzs > 0:
        parts.append(f"{uzs:,.0f} UZS")
    if usd > 0:
        parts.append(f"{usd:,.2f} USD")
    if parts:
        return "\n📝 Joriy qarzingiz: *" + " + ".join(parts) + "*"
    return "\n✅ Qarzingiz yo'q"


def _spent_line(customer: dict) -> str:
    uzs = float(customer.get('total_spent_uzs', 0))
    usd = float(customer.get('total_spent_usd', 0))
    parts = []
    if uzs > 0:
        parts.append(f"{uzs:,.0f} UZS")
    if usd > 0:
        parts.append(f"{usd:,.2f} USD")
    return " + ".join(parts) if parts else "0"


# ───────────────────────── Klaviaturalar ─────────────────────────

def customer_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="💳 Qarzlarim"),
        KeyboardButton(text="🧾 Sotuv tarixi"),
    )
    builder.row(KeyboardButton(text="📞 Admin bilan bog'lanish"))
    return builder.as_markup(resize_keyboard=True)


def link_request_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(
        text="📱 Telefon raqamim bilan ulanish",
        request_contact=True,
    ))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def admin_contact_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"📞 {ADMIN_PHONE_DISPLAY}",
        url=f"tel:{ADMIN_PHONE}",
    )
    return builder.as_markup()


async def _is_staff_user(user_id: int) -> bool:
    if user_id in ADMIN_CHAT_IDS or user_manager.is_allowed(user_id):
        return True
    try:
        return await api_client.is_bot_user_allowed(user_id)
    except Exception:
        return False


async def _greet_staff(message: Message):
    await message.answer(
        f"👋 Xush kelibsiz, {message.from_user.full_name}!\n\n"
        "🎈 BalonCRM xodim paneliga xush kelibsiz!",
        reply_markup=main_menu(),
    )


# ───────────────────────── /start handlers ─────────────────────────

@router.message(CommandStart(deep_link=True))
async def start_with_token(message: Message, command: CommandObject):
    """/start cust_<token> — deep link orqali avtomatik bog'lash."""
    if await _is_staff_user(message.from_user.id):
        await _greet_staff(message)
        return

    arg = (command.args or '').strip()
    if not arg.startswith('cust_'):
        await _greet_unlinked(message)
        return

    token = arg[len('cust_'):]
    full_name = message.from_user.full_name or ''
    data, code = await api_client.link_customer_by_token(
        token, message.from_user.id, full_name=full_name
    )

    if code == 200:
        name = data.get('name', 'Mijoz')
        debt_line = _debt_line(data)
        await message.answer(
            f"✅ Xush kelibsiz, *{name}*!\n\n"
            f"Telegram akkauntingiz muvaffaqiyatli tasdiqlandi.{debt_line}\n\n"
            f"Endi barcha sotuv cheklari va eslatmalarni shu yerda olasiz. 🎈",
            parse_mode='Markdown',
            reply_markup=customer_menu(),
        )
    elif code == 404:
        await message.answer(
            "❌ Bu havola yaroqsiz yoki muddati o'tgan.\n\n"
            "Iltimos, do'kondorga murojaat qiling.",
        )
    else:
        await message.answer("❌ Ulanish vaqtida xato yuz berdi. Keyinroq urinib ko'ring.")


@router.message(CommandStart())
async def start_no_arg(message: Message):
    """Oddiy /start — ulangan mijozga menyu, boshqalarga contact so'rash."""
    if await _is_staff_user(message.from_user.id):
        await _greet_staff(message)
        return

    customer = await api_client.get_customer_by_chat_id(message.from_user.id)
    if customer:
        name = customer.get('name', 'Mijoz')
        dl = _debt_line(customer).lstrip('\n')
        await message.answer(
            f"👋 Xush kelibsiz, *{name}*!\n\n"
            f"{dl}\n\n"
            f"Quyidagi tugmalardan foydalaning 👇",
            parse_mode='Markdown',
            reply_markup=customer_menu(),
        )
    else:
        await _greet_unlinked(message)


async def _greet_unlinked(message: Message):
    await message.answer(
        "👋 Salom! *BalonCRM* mijozlar botiga xush kelibsiz.\n\n"
        "Akkauntingizni bog'lash uchun pastdagi tugmani bosib, "
        "telefon raqamingizni ulashing 👇\n\n"
        "_(Agar do'kondor sizga maxsus havola yuborgan bo'lsa, "
        "shu havolani bosing — avtomatik bog'lanadi)_",
        parse_mode='Markdown',
        reply_markup=link_request_menu(),
    )


# ───────────────────────── Contact share ─────────────────────────

@router.message(F.contact)
async def contact_received(message: Message):
    if await _is_staff_user(message.from_user.id):
        await _greet_staff(message)
        return

    contact = message.contact
    if contact.user_id and contact.user_id != message.from_user.id:
        await message.answer(
            "❌ Faqat o'z telefon raqamingizni ulashing.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    phone = contact.phone_number
    full_name = message.from_user.full_name or contact.first_name or ''
    username = message.from_user.username or ''

    # 1. Avval staff (is_staff=True) ekanini tekshirish
    staff_result = await api_client.verify_staff_by_phone(
        phone, message.from_user.id, full_name=full_name, username=username
    )
    if staff_result.get('is_staff'):
        from keyboards import main_menu
        name = staff_result.get('full_name') or full_name or 'Xodim'
        await message.answer(
            f"✅ Xush kelibsiz, *{name}*!\n\n"
            f"Siz xodim sifatida tasdiqlandi.\n"
            f"🎈 BalonCRM boshqaruv paneliga xush kelibsiz!",
            parse_mode='Markdown',
            reply_markup=main_menu(),
        )
        return

    # 2. Customer tekshirish
    data, code = await api_client.link_customer_by_phone(
        phone, message.from_user.id, full_name=full_name
    )

    if code == 200:
        name = data.get('name', 'Mijoz')
        dl = _debt_line(data).lstrip('\n')
        await message.answer(
            f"✅ Telefon raqamingiz tasdiqlandi!\n\n"
            f"👤 Ism: *{name}*\n"
            f"📱 Telefon: {data.get('phone', phone)}\n"
            f"{dl}\n\n"
            f"Endi sotuv cheklari va qarz eslatmalarini shu yerda olasiz. 🎈",
            parse_mode='Markdown',
            reply_markup=customer_menu(),
        )
    elif code == 404:
        await message.answer(
            f"⚠️ *{phone}* raqami bilan ro'yxatdan o'tgan mijoz topilmadi.\n\n"
            f"Iltimos, do'kondorga murojaat qiling — sizni ro'yxatga qo'shadi.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove(),
        )
    elif code == 409:
        await message.answer(
            "⚠️ Bu raqam allaqachon boshqa Telegram akkauntga bog'langan.\n\n"
            "Agar bu xato bo'lsa, do'kondorga murojaat qiling.",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await message.answer(
            "❌ Ulanish vaqtida xato yuz berdi. Keyinroq urinib ko'ring.",
            reply_markup=ReplyKeyboardRemove(),
        )


# ───────────────────────── Mijoz menyu handlerlari ─────────────────────────

@router.message(F.text == "💳 Qarzlarim")
async def show_my_debt(message: Message):
    customer = await api_client.get_customer_by_chat_id(message.from_user.id)
    if not customer:
        await _greet_unlinked(message)
        return

    debt_uzs = float(customer.get('debt_uzs', 0))
    debt_usd = float(customer.get('debt_usd', 0))
    name = customer.get('name', '')
    spent = _spent_line(customer)

    if debt_uzs > 0 or debt_usd > 0:
        debt_parts = []
        if debt_uzs > 0:
            debt_parts.append(f"{debt_uzs:,.0f} UZS")
        if debt_usd > 0:
            debt_parts.append(f"{debt_usd:,.2f} USD")
        text = (
            f"💳 *{name} — hisob holati*\n\n"
            f"🔴 Joriy qarz: *{' + '.join(debt_parts)}*\n"
            f"🛒 Jami xarid: {spent}\n\n"
            f"Iltimos, qulay vaqtda to'lab qo'yishingizni so'raymiz. 🙏\n\n"
            f"To'lov yoki savol uchun do'kondorga murojaat qiling:"
        )
        await message.answer(text, parse_mode='Markdown', reply_markup=customer_menu())
        await message.answer(
            f"📞 Admin: {ADMIN_PHONE_DISPLAY}",
            reply_markup=admin_contact_keyboard(),
        )
    else:
        text = (
            f"✅ *{name} — hisob holati*\n\n"
            f"🟢 Qarz: *yo'q*\n"
            f"🛒 Jami xarid: {spent}\n\n"
            f"🎈 Rahmat, hisob-kitobingiz toza!"
        )
        await message.answer(text, parse_mode='Markdown', reply_markup=customer_menu())


@router.message(F.text == "🧾 Sotuv tarixi")
async def show_my_sales(message: Message):
    customer = await api_client.get_customer_by_chat_id(message.from_user.id)
    if not customer:
        await _greet_unlinked(message)
        return

    sales = await api_client.get_customer_sales(customer['id'])
    if not sales:
        await message.answer(
            "🧾 Sizda hali sotuvlar tarixi yo'q.",
            reply_markup=customer_menu(),
        )
        return

    shown = sales[:10]
    lines = [f"🧾 *Oxirgi {len(shown)} ta sotuv:*\n"]
    for s in shown:
        date = s.get('created_at', '')[:10]
        total = float(s.get('total', 0))
        method = s.get('payment_method_display', '')
        discount = float(s.get('discount', 0))
        line = f"• #{s['id']} — {date}\n  💰 {total:,.0f} so'm | {method}"
        if discount > 0:
            line += f" | 🏷 -{discount:,.0f}"
        lines.append(line)

    await message.answer('\n'.join(lines), parse_mode='Markdown', reply_markup=customer_menu())


@router.message(F.text == "📞 Admin bilan bog'lanish")
async def contact_admin(message: Message):
    await message.answer(
        f"📞 *Admin bilan bog'lanish*\n\n"
        f"Savol, muammo yoki to'lov uchun quyidagi raqamga qo'ng'iroq qiling:\n\n"
        f"☎️ {ADMIN_PHONE_DISPLAY}\n\n"
        f"Ish vaqti: har kuni 09:00 — 21:00",
        parse_mode='Markdown',
        reply_markup=admin_contact_keyboard(),
    )


# ───────────────────────── Eskirgan tugma mosligi ─────────────────────────

@router.message(F.text == "💳 Mening qarzim")
async def old_debt_button(message: Message):
    await show_my_debt(message)


@router.message(F.text == "🧾 Sotuvlar tarixi")
async def old_sales_button(message: Message):
    await show_my_sales(message)
