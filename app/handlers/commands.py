"""Telegram bot komandalar."""
import os
import random
from datetime import datetime

from aiogram import types
from aiogram.filters import Command

from app.core.config import ADMIN_ID, KEYWORDS, ONLINE_PAGES
from app.core import state
from app.services import kwork, browser


def is_admin(message: types.Message) -> bool:
    return message.from_user.id == ADMIN_ID


def register(dp):
    """Barcha komandalarni Dispatcher ga ro'yxatdan o'tkazadi."""

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        if not is_admin(message):
            return
        await message.answer(
            "🤖 <b>Kwork Bot Boshqaruv Paneli</b>\n\n"
            "📋 <b>Komandalar:</b>\n"
            "/status — Bot holati\n"
            "/stats — Statistika\n"
            "/projects — Proektlarni tekshirish\n"
            "/inbox — Inbox tekshirish\n"
            "/online — Online ping\n"
            "/keywords — Kalit so'zlar\n"
            "/addkw <code>so'z</code> — Kalit so'z qo'shish\n"
            "/delkw <code>so'z</code> — Kalit so'z o'chirish\n"
            "/autoresp — AI javob yoqish/o'chirish\n"
            "/pending — Kutayotgan javoblar\n"
            "/seo — SEO pozitsiyalar\n"
            "/cookie — Cookie yangilash\n"
            "/logs — Loglar\n"
            "/restart — Brauzerni qayta tushirish\n"
            "/help — Yordam"
        )

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        if not is_admin(message):
            return
        await message.answer(
            "ℹ️ <b>Yordam</b>\n\n"
            "1️⃣ <b>Online tutish</b> — har 7-10 daqiqada\n"
            "2️⃣ <b>Proekt monitoring</b> — har 5 daqiqada\n"
            "3️⃣ <b>Inbox monitoring</b> — har 2 daqiqada\n"
            "4️⃣ <b>Cookie auto-refresh</b> — har 2 soatda\n"
            "5️⃣ <b>SEO monitoring</b> — har 6 soatda\n\n"
            "✅ Yuborish — proektga javob\n"
            "✏️ Narx — narxni o'zgartirish\n"
            "❌ Bekor — javob yuborilmaydi"
        )

    @dp.message(Command("status"))
    async def cmd_status(message: types.Message):
        if not is_admin(message):
            return
        uptime = ""
        if state.stats["start_time"]:
            delta = datetime.now() - state.stats["start_time"]
            h, r = divmod(int(delta.total_seconds()), 3600)
            m, _ = divmod(r, 60)
            uptime = f"{h} soat {m} daqiqa"
        await message.answer(
            f"📊 <b>Bot Holati</b>\n\n"
            f"Holat: {'🟢 Faol' if state.monitoring_active else '🔴 To''xtagan'}\n"
            f"AI javob: {'🟢' if state.auto_respond else '🔴'}\n"
            f"Uptime: {uptime}\n"
            f"Kalit so'zlar: {len(KEYWORDS)} ta\n"
            f"Kutayotgan: {len(state.pending_responses)} ta"
        )

    @dp.message(Command("stats"))
    async def cmd_stats(message: types.Message):
        if not is_admin(message):
            return
        s = state.stats
        await message.answer(
            f"📈 <b>Statistika</b>\n\n"
            f"🌐 Online: {s['online_visits']}\n"
            f"📋 Proektlar: {s['projects_found']}\n"
            f"📨 Yuborildi: {s['projects_sent']}\n"
            f"✅ Javob: {s['responses_sent']}\n"
            f"📬 Inbox: {s['inbox_checks']}\n"
            f"💬 Xabarlar: {s['new_messages']}\n"
            f"🍪 Cookie: {s['cookie_refreshes']}\n"
            f"❌ Xatolar: {s['errors']}"
        )

    @dp.message(Command("keywords"))
    async def cmd_keywords(message: types.Message):
        if not is_admin(message):
            return
        kw_list = "\n".join(f"  {i+1}. <code>{kw}</code>" for i, kw in enumerate(KEYWORDS))
        await message.answer(f"🔑 <b>Kalit so'zlar ({len(KEYWORDS)} ta):</b>\n\n{kw_list}")

    @dp.message(Command("addkw"))
    async def cmd_addkw(message: types.Message):
        if not is_admin(message):
            return
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            return await message.answer("❌ /addkw <code>kalit_so'z</code>")
        kw = args[1].strip().lower()
        if kw in KEYWORDS:
            return await message.answer(f"⚠️ <code>{kw}</code> allaqachon bor")
        KEYWORDS.append(kw)
        await message.answer(f"✅ <code>{kw}</code> qo'shildi! ({len(KEYWORDS)} ta)")

    @dp.message(Command("delkw"))
    async def cmd_delkw(message: types.Message):
        if not is_admin(message):
            return
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            return await message.answer("❌ /delkw <code>kalit_so'z</code>")
        kw = args[1].strip().lower()
        if kw not in KEYWORDS:
            return await message.answer(f"⚠️ <code>{kw}</code> topilmadi")
        KEYWORDS.remove(kw)
        await message.answer(f"🗑 <code>{kw}</code> o'chirildi! ({len(KEYWORDS)} ta)")

    @dp.message(Command("autoresp"))
    async def cmd_autoresp(message: types.Message):
        if not is_admin(message):
            return
        state.auto_respond = not state.auto_respond
        await message.answer(f"🤖 AI javob: {'🟢 Yoqildi' if state.auto_respond else '🔴 O''chirildi'}")

    @dp.message(Command("projects"))
    async def cmd_projects(message: types.Message):
        if not is_admin(message) or not state.page:
            return
        await message.answer("🔍 Tekshirilmoqda...")
        from app.handlers.callbacks import notify
        count = await kwork.check_all_projects(notify)
        await message.answer(f"✅ {count} ta yangi proekt topildi.")

    @dp.message(Command("inbox"))
    async def cmd_inbox(message: types.Message):
        if not is_admin(message) or not state.page:
            return
        await message.answer("📬 Tekshirilmoqda...")
        from app.handlers.callbacks import notify
        await kwork.check_inbox(notify)
        await message.answer("✅ Inbox tekshirildi.")

    @dp.message(Command("online"))
    async def cmd_online(message: types.Message):
        if not is_admin(message) or not state.page:
            return
        url = random.choice(ONLINE_PAGES)
        await state.page.goto(url, timeout=60_000, wait_until="domcontentloaded")
        state.stats["online_visits"] += 1
        await message.answer(f"🟢 Online ping: {url}")

    @dp.message(Command("pending"))
    async def cmd_pending(message: types.Message):
        if not is_admin(message):
            return
        from app.handlers.callbacks import get_approve_keyboard
        if not state.pending_responses:
            return await message.answer("📭 Kutayotgan javob yo'q")
        for pid, data in state.pending_responses.items():
            await message.answer(
                f"⏳ <b>{data['title']}</b>\n💬 {data['response_text'][:300]}\n💰 {data['price']} ₽",
                reply_markup=get_approve_keyboard(pid),
            )

    @dp.message(Command("cookie"))
    async def cmd_cookie(message: types.Message):
        if not is_admin(message):
            return
        await browser.save_cookies()
        await message.answer(f"🍪 Cookie yangilandi! ({state.stats['cookie_refreshes']})")

    @dp.message(Command("seo"))
    async def cmd_seo(message: types.Message):
        if not is_admin(message) or not state.page:
            return
        await message.answer("🔍 SEO tekshirilmoqda...")
        result = await kwork.check_seo()
        await message.answer(result)

    @dp.message(Command("logs"))
    async def cmd_logs(message: types.Message):
        if not is_admin(message):
            return
        if os.path.exists("bot.log"):
            with open("bot.log") as f:
                lines = f.readlines()[-15:]
            await message.answer("📄 <b>Loglar:</b>\n\n" + "\n".join(f"<code>{l.strip()}</code>" for l in lines))
        else:
            await message.answer("📄 Log topilmadi")

    @dp.message(Command("restart"))
    async def cmd_restart(message: types.Message):
        if not is_admin(message):
            return
        await message.answer("🔄 Qayta ishga tushirilmoqda...")
        await browser.setup()
        await message.answer("✅ Tayyor!" if state.page else "❌ Xato!")
