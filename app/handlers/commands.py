"""Команды Telegram бота."""
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

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        if not is_admin(message):
            return
        await message.answer(
            "🤖 <b>Панель управления Kwork Bot</b>\n\n"
            "📋 <b>Команды:</b>\n"
            "/status — Статус бота\n"
            "/stats — Статистика\n"
            "/projects — Проверить проекты\n"
            "/inbox — Проверить входящие\n"
            "/online — Онлайн пинг\n"
            "/keywords — Список ключевых слов\n"
            "/addkw <code>слово</code> — Добавить ключевое слово\n"
            "/delkw <code>слово</code> — Удалить ключевое слово\n"
            "/autoresp — Вкл/выкл AI ответ\n"
            "/pending — Ожидающие ответы\n"
            "/seo — SEO позиции\n"
            "/cookie — Обновить cookie\n"
            "/logs — Последние логи\n"
            "/restart — Перезапустить браузер\n"
            "/help — Помощь"
        )

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        if not is_admin(message):
            return
        await message.answer(
            "ℹ️ <b>Помощь</b>\n\n"
            "Бот выполняет 5 задач:\n"
            "1️⃣ <b>Онлайн</b> — каждые 7-10 мин\n"
            "2️⃣ <b>Мониторинг проектов</b> — каждые 5 мин\n"
            "3️⃣ <b>Мониторинг входящих</b> — каждые 2 мин\n"
            "4️⃣ <b>Обновление cookie</b> — каждые 2 часа\n"
            "5️⃣ <b>SEO мониторинг</b> — каждые 6 часов\n\n"
            "🤖 <b>AI ответ:</b>\n"
            "При новом проекте Claude пишет отклик.\n"
            "  ✅ Отправить — отправить отклик\n"
            "  ✏️ Цена — изменить цену\n"
            "  ❌ Отмена — не отправлять"
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
            uptime = f"{h} ч {m} мин"
        await message.answer(
            f"📊 <b>Статус бота</b>\n\n"
            f"Состояние: {'🟢 Активен' if state.monitoring_active else '🔴 Остановлен'}\n"
            f"AI ответ: {'🟢 Включён' if state.auto_respond else '🔴 Выключен'}\n"
            f"Аптайм: {uptime}\n"
            f"Ключевые слова: {len(KEYWORDS)} шт\n"
            f"Ожидают ответа: {len(state.pending_responses)} шт"
        )

    @dp.message(Command("stats"))
    async def cmd_stats(message: types.Message):
        if not is_admin(message):
            return
        s = state.stats
        await message.answer(
            f"📈 <b>Статистика</b>\n\n"
            f"🌐 Онлайн визиты: {s['online_visits']}\n"
            f"📋 Проектов найдено: {s['projects_found']}\n"
            f"📨 Отправлено в TG: {s['projects_sent']}\n"
            f"✅ Откликов отправлено: {s['responses_sent']}\n"
            f"📬 Проверок входящих: {s['inbox_checks']}\n"
            f"💬 Новых сообщений: {s['new_messages']}\n"
            f"🍪 Обновлений cookie: {s['cookie_refreshes']}\n"
            f"❌ Ошибок: {s['errors']}"
        )

    @dp.message(Command("keywords"))
    async def cmd_keywords(message: types.Message):
        if not is_admin(message):
            return
        kw_list = "\n".join(f"  {i+1}. <code>{kw}</code>" for i, kw in enumerate(KEYWORDS))
        await message.answer(f"🔑 <b>Ключевые слова ({len(KEYWORDS)} шт):</b>\n\n{kw_list}")

    @dp.message(Command("addkw"))
    async def cmd_addkw(message: types.Message):
        if not is_admin(message):
            return
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            return await message.answer("❌ Формат: /addkw <code>слово</code>")
        kw = args[1].strip().lower()
        if kw in KEYWORDS:
            return await message.answer(f"⚠️ <code>{kw}</code> уже есть")
        KEYWORDS.append(kw)
        await message.answer(f"✅ <code>{kw}</code> добавлено! Всего: {len(KEYWORDS)} шт")

    @dp.message(Command("delkw"))
    async def cmd_delkw(message: types.Message):
        if not is_admin(message):
            return
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            return await message.answer("❌ Формат: /delkw <code>слово</code>")
        kw = args[1].strip().lower()
        if kw not in KEYWORDS:
            return await message.answer(f"⚠️ <code>{kw}</code> не найдено")
        KEYWORDS.remove(kw)
        await message.answer(f"🗑 <code>{kw}</code> удалено! Осталось: {len(KEYWORDS)} шт")

    @dp.message(Command("autoresp"))
    async def cmd_autoresp(message: types.Message):
        if not is_admin(message):
            return
        state.auto_respond = not state.auto_respond
        await message.answer(f"🤖 AI ответ: {'🟢 Включён' if state.auto_respond else '🔴 Выключен'}")

    @dp.message(Command("projects"))
    async def cmd_projects(message: types.Message):
        if not is_admin(message) or not state.page:
            return
        await message.answer("🔍 Проверяю проекты...")
        from app.handlers.callbacks import notify
        count = await kwork.check_all_projects(notify)
        await message.answer(f"✅ Найдено {count} новых проектов.")

    @dp.message(Command("inbox"))
    async def cmd_inbox(message: types.Message):
        if not is_admin(message) or not state.page:
            return
        await message.answer("📬 Проверяю входящие...")
        from app.handlers.callbacks import notify
        await kwork.check_inbox(notify)
        await message.answer("✅ Входящие проверены.")

    @dp.message(Command("online"))
    async def cmd_online(message: types.Message):
        if not is_admin(message) or not state.page:
            return
        url = random.choice(ONLINE_PAGES)
        await state.page.goto(url, timeout=60_000, wait_until="domcontentloaded")
        state.stats["online_visits"] += 1
        await message.answer(f"🟢 Онлайн пинг отправлен!\nСтраница: {url}")

    @dp.message(Command("pending"))
    async def cmd_pending(message: types.Message):
        if not is_admin(message):
            return
        from app.handlers.callbacks import get_approve_keyboard
        if not state.pending_responses:
            return await message.answer("📭 Нет ожидающих ответов")
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
        await message.answer(f"🍪 Cookie обновлены! Всего обновлений: {state.stats['cookie_refreshes']}")

    @dp.message(Command("seo"))
    async def cmd_seo(message: types.Message):
        if not is_admin(message) or not state.page:
            return
        await message.answer("🔍 Проверяю SEO позиции...")
        result = await kwork.check_seo()
        await message.answer(result)

    @dp.message(Command("logs"))
    async def cmd_logs(message: types.Message):
        if not is_admin(message):
            return
        if os.path.exists("bot.log"):
            with open("bot.log") as f:
                lines = f.readlines()[-15:]
            await message.answer("📄 <b>Логи:</b>\n\n" + "\n".join(f"<code>{l.strip()}</code>" for l in lines))
        else:
            await message.answer("📄 Лог не найден")

    @dp.message(Command("restart"))
    async def cmd_restart(message: types.Message):
        if not is_admin(message):
            return
        await message.answer("🔄 Перезапуск браузера...")
        await browser.setup()
        await message.answer("✅ Готово!" if state.page else "❌ Ошибка!")
