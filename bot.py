"""Kwork Bot — Aiogram + Claude AI + Playwright."""
import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.core.config import TELEGRAM_TOKEN, KEYWORDS
from app.core import state
from app.services import browser, scheduler
from app.handlers import commands, callbacks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Handler larni ro'yxatdan o'tkazish
commands.register(dp)
callbacks.register(dp)
callbacks.set_bot(bot)


async def on_startup():
    state.stats["start_time"] = datetime.now()

    log.info("Brauzer sozlanmoqda...")
    ok = await browser.setup()
    if not ok:
        await callbacks.notify("❌ Brauzer xatosi! Cookie yangilash kerak.")
        return

    state.monitoring_active = True
    scheduler.start_all(callbacks.notify)

    await callbacks.notify(
        "🚀 <b>Kwork Bot ishga tushdi!</b>\n\n"
        f"🤖 Claude AI: {'🟢' if state.auto_respond else '🔴'}\n"
        f"🔑 Kalit so'zlar: {len(KEYWORDS)} ta\n"
        f"🍪 Cookie refresh: 🟢 (2 soat)\n"
        f"📊 SEO: 🟢 (6 soat)\n"
        f"📋 /help — komandalar"
    )
    log.info("Bot ishga tushdi!")


async def main():
    log.info("=" * 50)
    log.info("KWORK BOT — Aiogram + Claude AI + Playwright")
    log.info("=" * 50)

    async def startup_wrapper():
        await asyncio.sleep(2)
        await on_startup()

    asyncio.create_task(startup_wrapper())
    await dp.start_polling(bot, allowed_updates=["message", "callback_query", "edited_message"])


if __name__ == "__main__":
    asyncio.run(main())
