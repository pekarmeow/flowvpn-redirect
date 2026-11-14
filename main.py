"""FlowVPN -> MonoVPN: информационный бот без доступа к VPN и платежам.

Использует только BOT_TOKEN старого FlowVPN бота из переменных хостинга.
Не запускает обслуживание ключей, автопродления и никакие задачи миграции.
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonCommands,
    Message,
)

NEW_BOT_URL = "https://t.me/monoovpn_bot"

WELCOME_TEXT = (
    "🔔 <b>FlowVPN переехал в MonoVPN!</b>\n\n"
    "💙 Мы обновились и теперь работаем под новым названием — <b>MonoVPN</b>.\n\n"
    "✅ Ваши VPN-ключи, действующие подписки и баланс перенесены в нового бота.\n"
    "🚀 В MonoVPN вас ждут обновлённый Mini App, статус серверов и тест скорости.\n\n"
    "👇 <b>Нажмите кнопку ниже, затем «Запустить» в новом боте.</b> "
    "Все ваши данные доступны с этого же Telegram-аккаунта."
)

REDIRECT_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Перейти в MonoVPN", url=NEW_BOT_URL)]
    ]
)

router = Router()


@router.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=REDIRECT_KEYBOARD)


@router.message()
async def on_other_message(message: Message) -> None:
    """Отвечаем и на старые команды и на сообщения в устаревшем чате."""
    await message.answer(WELCOME_TEXT, reply_markup=REDIRECT_KEYBOARD)


@router.callback_query()
async def on_old_callback(callback: CallbackQuery) -> None:
    """Объясняем, куда перейти при нажатии старой inline-кнопки."""
    await callback.answer("FlowVPN переехал в MonoVPN — ссылка придёт сообщением.")
    await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=WELCOME_TEXT,
        reply_markup=REDIRECT_KEYBOARD,
    )


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "Переменная BOT_TOKEN не установлена. Укажите токен СТАРОГО FlowVPN бота в Bothost."
        )

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    try:
        await bot.delete_webhook(drop_pending_updates=False)
        # Старая кнопка «Открыть» Mini App больше не должна вести в старое приложение.
        try:
            await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
            await bot.set_my_commands([
                BotCommand(command="start", description="Перейти в MonoVPN"),
                BotCommand(command="help", description="Где теперь наш VPN"),
            ])
        except Exception:
            logging.exception("Не удалось изменить меню; ответы /start продолжат работать")

        logging.info("FlowVPN redirect bot running; target: @monoovpn_bot")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
