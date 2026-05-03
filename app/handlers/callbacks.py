"""Инлайн кнопки и подтверждение AI ответов."""
import logging

from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.core.config import ADMIN_ID
from app.core import state
from app.services import kwork, claude

log = logging.getLogger(__name__)

_bot = None


def set_bot(bot):
    global _bot
    _bot = bot


def get_approve_keyboard(project_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data=f"approve:{project_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"reject:{project_id}"),
        ],
        [
            InlineKeyboardButton(text="✏️ Изменить цену", callback_data=f"editprice:{project_id}"),
        ],
    ])


async def notify(text: str, reply_markup=None):
    try:
        await _bot.send_message(ADMIN_ID, text, reply_markup=reply_markup)
    except Exception as e:
        log.error("Ошибка уведомления: %s", e)
        try:
            await _bot.send_message(ADMIN_ID, text, reply_markup=reply_markup, parse_mode=None)
        except Exception:
            pass


async def prepare_ai_response(project_id, title, description, budget, url, notify_fn):
    """Claude AI готовит отклик и отправляет админу на подтверждение."""
    try:
        log.info("Claude AI генерирует отклик: %s", project_id)
        ai = await claude.generate_response(title, description, budget)

        state.pending_responses[project_id] = {
            "url": url,
            "title": title,
            "response_text": ai["response_text"],
            "price": ai["suggested_price"],
        }

        msg = (
            f"🤖 <b>AI отклик готов!</b>\n\n"
            f"📋 <b>{title}</b>\n\n"
            f"💬 <b>Текст отклика:</b>\n<i>{ai['response_text']}</i>\n\n"
            f"💰 Цена: <b>{ai['suggested_price']} ₽</b>\n"
            f"📊 Сложность: {ai['complexity']} | ⏱ Срок: {ai['estimated_days']} дн.\n\n"
            f"🔗 <a href=\"{url}\">Открыть проект</a>\n\n"
            f"👇 <b>Подтверждаете?</b>"
        )
        await notify_fn(msg, reply_markup=get_approve_keyboard(project_id))
    except Exception as e:
        state.stats["errors"] += 1
        log.error("Ошибка AI: %s", e)


def register(dp):

    @dp.callback_query(F.data.startswith("approve:"))
    async def cb_approve(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            return
        pid = callback.data.split(":", 1)[1]
        data = state.pending_responses.get(pid)
        if not data:
            return await callback.answer("⚠️ Не найдено")

        await callback.answer("⏳ Отправляю...")
        await callback.message.edit_reply_markup(reply_markup=None)

        ok = await kwork.send_response(data["url"], data["response_text"], data["price"])
        if ok:
            state.stats["responses_sent"] += 1
            del state.pending_responses[pid]
            await callback.message.edit_text(callback.message.text + "\n\n✅ <b>ОТПРАВЛЕНО!</b>")
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Повторить", callback_data=f"approve:{pid}"),
                    InlineKeyboardButton(text="❌ Отмена", callback_data=f"reject:{pid}"),
                ],
            ])
            await callback.message.edit_reply_markup(reply_markup=kb)
            await callback.message.reply("❌ Ошибка отправки! Попробуйте снова.")

    @dp.callback_query(F.data.startswith("reject:"))
    async def cb_reject(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            return
        pid = callback.data.split(":", 1)[1]
        state.pending_responses.pop(pid, None)
        await callback.answer("❌ Отменено")
        await callback.message.edit_text(callback.message.text + "\n\n❌ <b>ОТМЕНЕНО</b>")

    @dp.callback_query(F.data.startswith("editprice:"))
    async def cb_editprice(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            return
        pid = callback.data.split(":", 1)[1]
        if pid not in state.pending_responses:
            return await callback.answer("⚠️ Не найдено")
        await callback.answer()
        await callback.message.reply(f"✏️ Введите новую цену:\n<code>цена {pid} 5000</code>")

    @dp.message(F.text.startswith("цена "))
    async def handle_price_edit(message: types.Message):
        if message.from_user.id != ADMIN_ID:
            return
        parts = message.text.split()
        if len(parts) < 3:
            return await message.answer("❌ Формат: <code>цена ID 5000</code>")
        pid, price = parts[1], parts[2]
        if pid not in state.pending_responses:
            return await message.answer("⚠️ Не найдено")
        state.pending_responses[pid]["price"] = price
        data = state.pending_responses[pid]
        await message.answer(
            f"✅ Цена обновлена: <b>{price} ₽</b>\n📋 {data['title']}",
            reply_markup=get_approve_keyboard(pid),
        )
