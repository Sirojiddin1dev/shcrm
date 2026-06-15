import asyncio
import logging
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.fsm.storage.memory import MemoryStorage
from typing import Any, Callable, Awaitable
from config import BOT_TOKEN, ADMIN_CHAT_IDS
from keyboards import main_menu
from handlers import (
    sale_handler, purchase_handler, stats_handler,
    admin_handler, customer_handler, staff_handler,
)
import api_client
import user_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Customerga ochiq buyruq/matnlar (xodim ruxsatisiz ham ishlaydi)
CUSTOMER_PUBLIC_TEXTS = {
    "📱 Telefon raqamim bilan ulanish",
    # Mijoz tugmalari
    "💳 Qarzlarim",
    "🧾 Sotuv tarixi",
    "📞 Admin bilan bog'lanish",
    # Eski mijoz tugmalari
    "💳 Mening qarzim",
    "🧾 Sotuvlar tarixi",
}


class AccessMiddleware(BaseMiddleware):
    """Ruxsatlarni boshqarish:
      1) Admin — barcha tugmalar
      2) Bot user (xodim) — sotuv/harid/statistika tugmalari
      3) Mijoz (Customer.telegram_chat_id) — faqat customer menyusi
      4) Boshqa — faqat /start, /myid va contact share
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, 'from_user', None)
        if user is None and hasattr(event, 'message') and event.message:
            user = event.message.from_user
        if user is None:
            return await handler(event, data)

        user_id = user.id

        # 1) Admin
        if user_id in ADMIN_CHAT_IDS:
            return await handler(event, data)

        # 2) Ochiq buyruqlar (har kim uchun)
        if isinstance(event, Message):
            text = (event.text or '').strip()
            if text.startswith('/start') or text == '/myid' or text == '/help':
                return await handler(event, data)
            if event.contact is not None:
                return await handler(event, data)
            if text in CUSTOMER_PUBLIC_TEXTS:
                return await handler(event, data)

        # 3) Xodim (TelegramBotUser)
        try:
            if await api_client.is_bot_user_allowed(user_id):
                return await handler(event, data)
        except Exception:
            logger.exception("TelegramBotUser tekshirishda xato")
        if user_manager.is_allowed(user_id):
            return await handler(event, data)

        # 4) Mijoz (Customer.telegram_chat_id)
        try:
            customer = await api_client.get_customer_by_chat_id(user_id)
            if customer:
                return await handler(event, data)
        except Exception:
            logger.exception("Customer tekshirishda xato")

        # Ruxsat yo'q
        if isinstance(event, Message):
            await event.answer(
                f"⛔ Sizda botdan foydalanish uchun ruxsat yo'q.\n\n"
                f"📱 Mijoz bo'lsangiz: telefon raqamingizni ulashing — `/start`\n"
                f"👨‍💼 Xodim bo'lsangiz: adminga ID yuboring — `/myid`",
                parse_mode='Markdown',
            )
        elif isinstance(event, CallbackQuery):
            await event.answer("Ruxsat yo'q", show_alert=True)
        return None


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(AccessMiddleware())
    dp.callback_query.middleware(AccessMiddleware())

    # Routerlar tartibi muhim: customer_handler /start ni avval ushlab oladi
    dp.include_router(customer_handler.router)
    dp.include_router(admin_handler.router)
    dp.include_router(sale_handler.router)
    dp.include_router(purchase_handler.router)
    dp.include_router(stats_handler.router)
    dp.include_router(staff_handler.router)

    @dp.message(lambda m: m.text and m.text.startswith('/start'))
    async def cmd_start_fallback(message: Message):
        """Faqat customer_handler /start ni ushlamasa (xodim/admin uchun)."""
        user_id = message.from_user.id
        is_staff = user_id in ADMIN_CHAT_IDS or user_manager.is_allowed(user_id)
        if not is_staff:
            try:
                is_staff = await api_client.is_bot_user_allowed(user_id)
            except Exception:
                is_staff = False
        if is_staff:
            await message.answer(
                f"👋 Xush kelibsiz, {message.from_user.full_name}!\n\n"
                "🎈 BalonCRM xodim paneliga xush kelibsiz!",
                reply_markup=main_menu(),
            )
            return

        await customer_handler.start_no_arg(message)

    logger.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())
