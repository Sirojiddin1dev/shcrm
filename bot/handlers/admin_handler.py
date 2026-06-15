from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import api_client
import user_manager
from config import ADMIN_CHAT_IDS

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_CHAT_IDS


@router.message(Command('adduser'))
async def cmd_add_user(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Faqat adminlar uchun")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "Ishlatish: `/adduser <user_id> [ism]`\n\n"
            "Misol: `/adduser 123456789 Ali Valiyev`",
            parse_mode='Markdown'
        )
        return

    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("User ID faqat raqam bo'lishi kerak")
        return

    name = ' '.join(parts[2:]) if len(parts) > 2 else ''
    display_name = name or "Ko'rsatilmagan"

    try:
        data, response_status = await api_client.add_bot_user(user_id, full_name=name)
    except Exception:
        added = user_manager.add_user(user_id, name=name, added_by=message.from_user.id)
        if added:
            await message.answer(
                f"Foydalanuvchi lokal ro'yxatga qo'shildi.\n"
                f"ID: `{user_id}`\n"
                f"Ism: {display_name}\n\n"
                "Backend API ishlamagani uchun admin panelga yozilmadi.",
                parse_mode='Markdown'
            )
        else:
            await message.answer(f"Bu foydalanuvchi (`{user_id}`) allaqachon ruxsatga ega")
        return

    if response_status == 201:
        await message.answer(
            f"Foydalanuvchi qo'shildi.\n"
            f"ID: `{user_id}`\n"
            f"Ism: {display_name}\n\n"
            "Endi u botdan foydalana oladi va admin panelda ko'rinadi.",
            parse_mode='Markdown'
        )
    else:
        detail = data.get('detail') or data.get('chat_id') or "Allaqachon mavjud bo'lishi mumkin"
        await message.answer(f"Foydalanuvchi qo'shilmadi (`{user_id}`): {detail}", parse_mode='Markdown')


@router.message(Command('removeuser'))
async def cmd_remove_user(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Faqat adminlar uchun")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Ishlatish: `/removeuser <user_id>`", parse_mode='Markdown')
        return

    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("User ID faqat raqam bo'lishi kerak")
        return

    try:
        response_status = await api_client.remove_bot_user(user_id)
    except Exception:
        response_status = 500

    removed_local = user_manager.remove_user(user_id)
    if response_status == 204 or removed_local:
        await message.answer(f"Foydalanuvchi `{user_id}` o'chirildi", parse_mode='Markdown')
    else:
        await message.answer(f"Bu foydalanuvchi (`{user_id}`) ro'yxatda yo'q", parse_mode='Markdown')


@router.message(Command('users'))
async def cmd_list_users(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Faqat adminlar uchun")
        return

    try:
        users = await api_client.list_bot_users()
    except Exception:
        users = user_manager.list_users()

    if not users:
        await message.answer("Hozircha ruxsat berilgan foydalanuvchi yo'q")
        return

    lines = [f"*Ruxsat berilgan foydalanuvchilar ({len(users)} ta):*\n"]
    for user in users:
        chat_id = user.get('chat_id') or user.get('id')
        name = user.get('full_name') or user.get('name') or 'Nomsiz'
        status = '' if user.get('is_active', True) else ' (nofaol)'
        lines.append(f"- `{chat_id}` - {name}{status}")

    await message.answer('\n'.join(lines), parse_mode='Markdown')


@router.message(Command('myid'))
async def cmd_my_id(message: Message):
    await message.answer(
        f"Sizning Telegram ID:\n`{message.from_user.id}`\n\n"
        f"Ism: {message.from_user.full_name}\n\n"
        "Admindan botdan foydalanish uchun shu ID ni yuboring.",
        parse_mode='Markdown'
    )


@router.message(Command('help'))
async def cmd_help(message: Message):
    if is_admin(message.from_user.id):
        await message.answer(
            "*Admin buyruqlari:*\n\n"
            "`/adduser <id> [ism]` - foydalanuvchi qo'shish\n"
            "`/removeuser <id>` - foydalanuvchini o'chirish\n"
            "`/users` - ruxsatlilar ro'yxati\n"
            "`/myid` - o'z ID ni ko'rish\n\n"
            "Tugmalardan sotuvlarni boshqarish mumkin.",
            parse_mode='Markdown'
        )
    else:
        await message.answer(
            "Yordam uchun adminga murojaat qiling.\n\n"
            "ID ni admin ga yuboring: `/myid`",
            parse_mode='Markdown'
        )
