"""Работа с Kwork.ru — мониторинг, SEO, отправка откликов."""
import asyncio
import re
import random
import hashlib
import logging

from app.core import state
from app.core.config import KEYWORDS, ONLINE_PAGES
from app.services.human import human_fill, human_scroll, human_pause, random_mouse_move
from app.services import claude

log = logging.getLogger(__name__)


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


async def get_full_description(url: str) -> str:
    """Получает полное описание проекта со страницы."""
    if not state.page:
        return ""
    try:
        await state.page.goto(url, timeout=60_000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        desc = await state.page.evaluate("""() => {
            const selectors = ['.wants-card__description-text', '.breakwords',
                '.want-card__description', '.kwork-detail-description', '[class*="description"]'];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.innerText.trim().length > 20) return el.innerText.trim();
            }
            return '';
        }""")
        return desc or ""
    except Exception as e:
        log.warning("Ошибка описания [%s]: %s", url, e)
        return ""


async def check_all_projects(notify_fn) -> int:
    """Проверяет новые проекты по всем ключевым словам."""
    if not state.page:
        return 0

    total_new = 0
    kw_list = KEYWORDS.copy()
    random.shuffle(kw_list)
    kw_list = kw_list[:random.randint(max(3, len(kw_list) // 2), len(kw_list))]

    for kw in kw_list:
        try:
            url = f"https://kwork.ru/projects?keyword={kw}&a=1"
            await state.page.goto(url, timeout=60_000, wait_until="domcontentloaded")
            await asyncio.sleep(3)

            if "login" in state.page.url:
                await notify_fn("⚠️ Сессия истекла! Нужно обновить cookie.")
                return total_new

            projects_data = await state.page.evaluate("""() => {
                const cards = document.querySelectorAll('.want-card');
                return Array.from(cards).map(card => {
                    const linkEl = card.querySelector('h1 a, h2 a, .wants-card__header-title a');
                    if (!linkEl) return null;
                    const href = linkEl.getAttribute('href') || '';
                    const title = linkEl.innerText?.trim() || '';
                    const cardText = card.innerText || '';
                    const offersMatch = cardText.match(/Предложений[:\\s]*(\\d+)/);
                    const offers = offersMatch ? parseInt(offersMatch[1]) : 999;
                    const priceEl = card.querySelector('.wants-card__price');
                    const price = priceEl ? priceEl.innerText.trim().replace(/\\s+/g, ' ') : '';
                    const timeEl = card.querySelector('.want-card__informers');
                    const timeText = timeEl ? timeEl.innerText.trim().replace(/\\s+/g, ' ') : '';
                    const descEl = card.querySelector('.wants-card__description-text .d-inline');
                    const desc = descEl ? descEl.innerText.trim() : '';
                    return { href, title, offers, price, timeText, desc };
                }).filter(x => x && x.href);
            }""")

            state.stats["projects_found"] += len(projects_data)

            for p in projects_data:
                try:
                    href = p["href"]
                    project_id = href.strip("/").split("/")[-1]
                    if project_id in state.seen_project_ids:
                        continue
                    state.seen_project_ids.add(project_id)
                    if p["offers"] >= 5:
                        continue

                    full_url = f"https://kwork.ru{href}" if href.startswith("/") else href
                    desc = await get_full_description(full_url)
                    if not desc:
                        desc = p["desc"]

                    desc_short = escape_html(desc)[:800]
                    offers_text = f"📊 Предложений: {p['offers']}" if p["offers"] < 999 else ""
                    msg = (
                        f"🆕 <b>{p['title']}</b>\n\n"
                        f"📝 {desc_short}\n\n"
                        f"💰 {p['price']}\n"
                        f"{offers_text}\n"
                        f"ℹ️ {p['timeText']}\n\n"
                        f"🔍 Ключевое слово: <code>{kw}</code>\n"
                        f"🔗 <a href=\"{full_url}\">Открыть проект</a>"
                    )
                    await notify_fn(msg)
                    state.stats["projects_sent"] += 1
                    total_new += 1

                    if state.auto_respond:
                        from app.handlers.callbacks import prepare_ai_response
                        await prepare_ai_response(
                            project_id, p["title"], desc, p["price"], full_url, notify_fn,
                        )
                    await asyncio.sleep(1)
                except Exception as e:
                    log.warning("Ошибка карточки: %s", e)

            await asyncio.sleep(random.uniform(2, 4))
        except Exception as e:
            state.stats["errors"] += 1
            log.error("Ошибка проверки [%s]: %s", kw, e)

    return total_new


async def send_response(url: str, response_text: str, price: str) -> bool:
    """Отправляет отклик на проект (с имитацией человека)."""
    if not state.page:
        return False
    try:
        await state.page.goto(url, timeout=60_000, wait_until="domcontentloaded")
        await human_pause()
        await random_mouse_move(state.page)
        await human_scroll(state.page)

        btn = await state.page.query_selector(
            'button:has-text("Откликнуться"), a:has-text("Откликнуться"), '
            '[class*="want-btn"], [class*="respond"]'
        )
        if not btn:
            return False

        await random_mouse_move(state.page)
        await asyncio.sleep(random.uniform(1, 3))
        await btn.click()
        await asyncio.sleep(random.uniform(2, 4))

        textarea = await state.page.query_selector(
            'textarea[placeholder*="опишите"], textarea[name*="message"], '
            'textarea[class*="form"], div[contenteditable="true"]'
        )
        if not textarea:
            return False

        await human_fill(textarea, response_text)

        price_input = await state.page.query_selector(
            'input[name*="price"], input[placeholder*="стоимость"], '
            'input[placeholder*="цен"], input[type="number"]'
        )
        if price_input:
            await price_input.click()
            await asyncio.sleep(random.uniform(0.3, 0.8))
            await price_input.fill("")
            await price_input.type(str(price), delay=random.randint(50, 100))

        await asyncio.sleep(random.uniform(2, 5))

        send_btn = await state.page.query_selector(
            'button:has-text("Отправить"), button:has-text("Откликнуться"), button[type="submit"]'
        )
        if send_btn:
            await random_mouse_move(state.page)
            await send_btn.click()
            await asyncio.sleep(random.uniform(3, 6))
            return True
    except Exception as e:
        state.stats["errors"] += 1
        log.error("Ошибка отклика: %s", e)
    return False


async def check_inbox(notify_fn):
    """Проверяет новые сообщения во входящих."""
    if not state.page:
        return
    try:
        await state.page.goto("https://kwork.ru/inbox", timeout=60_000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        if "login" in state.page.url:
            await notify_fn("⚠️ Сессия истекла!")
            return

        state.stats["inbox_checks"] += 1
        data = await state.page.evaluate("""() => {
            const items = document.querySelectorAll('.chat__list-item');
            return Array.from(items).map(item => {
                const user = item.querySelector('.chat__list-user')?.innerText?.trim() || '';
                const msg  = item.querySelector('.chat__list-message')?.innerText?.trim() || '';
                const date = item.querySelector('.chat__list-date')?.innerText?.trim() || '';
                return { user, msg, date };
            }).filter(x => x.user);
        }""")

        for c in data:
            user, msg, date = c["user"], c["msg"], c["date"]
            if msg.startswith("Вы:") or not msg:
                state.prev_inbox_state[user] = hashlib.md5((msg + date).encode()).hexdigest()
                continue
            current_hash = hashlib.md5((msg + date).encode()).hexdigest()
            prev_hash = state.prev_inbox_state.get(user)
            if prev_hash is None:
                state.prev_inbox_state[user] = current_hash
            elif prev_hash != current_hash:
                state.prev_inbox_state[user] = current_hash
                state.stats["new_messages"] += 1
                await notify_fn(
                    f"💬 <b>Новое сообщение!</b>\n\n👤 <b>{user}</b>\n🕐 {date}\n\n"
                    f"📩 {msg}\n\n🔗 <a href=\"https://kwork.ru/inbox\">Входящие</a>"
                )
                await asyncio.sleep(0.5)
    except Exception as e:
        state.stats["errors"] += 1
        log.error("Ошибка входящих: %s", e)


async def online_ping():
    """Поддерживает онлайн статус на Kwork."""
    if not state.page:
        return
    try:
        url = random.choice(ONLINE_PAGES)
        await state.page.goto(url, timeout=60_000, wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(2, 5))
        await random_mouse_move(state.page)
        await human_scroll(state.page)
        await human_pause()

        if random.random() < 0.3:
            link = await state.page.query_selector('a[href*="kwork.ru"]:not([href*="logout"])')
            if link:
                await link.click()
                await asyncio.sleep(random.uniform(3, 7))
                await human_scroll(state.page)

        state.stats["online_visits"] += 1
        log.info("Онлайн пинг: %s", url)
    except Exception as e:
        state.stats["errors"] += 1
        log.error("Ошибка онлайн: %s", e)


async def check_seo() -> str:
    """Проверяет позиции кворков в поиске."""
    if not state.page:
        return "❌ Браузер не запущен"
    try:
        await state.page.goto("https://kwork.ru/manage_kworks", timeout=60_000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        if "login" in state.page.url:
            return "⚠️ Сессия истекла!"

        await state.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)

        my_kworks = await state.page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('.js-kwork-card').forEach(card => {
                const id = card.getAttribute('data-kwork-id') || '';
                const titleEl = card.querySelector('.manage-kworks-item__title a span, .manage-kworks-item__title a, h3 a');
                const title = titleEl ? titleEl.innerText.trim() : '';
                if (id && title) results.push({ title, id });
            });
            return results;
        }""")

        if not my_kworks:
            return "📭 Кворки не найдены."

        STOP_WORDS = {
            "для", "на", "под", "или", "и", "в", "с", "из", "от", "по", "к",
            "любого", "любой", "любые", "ваш", "ваши", "вашего",
            "разработка", "разработаю", "создание", "создам", "напишу",
            "доработка", "настройка", "адаптивная", "бекенд", "верстка",
            "сайта", "приложения", "языке", "готовой", "базе",
        }

        results = [f"📊 <b>SEO Позиции</b>\n", f"🔍 Кворков: {len(my_kworks)} шт\n"]

        for kw in my_kworks[:10]:
            tech_words = re.findall(
                r'\b(?:python|django|fastapi|flask|react|next\.?js|vue\.?js|telegram|whatsapp|api|bot|бот|crm|seo)\b',
                kw["title"], re.IGNORECASE,
            )
            if tech_words:
                search_term = " ".join(tech_words[:2])
            else:
                words = [w for w in kw["title"].split() if w.lower().rstrip(",:") not in STOP_WORDS and len(w) > 2]
                search_term = " ".join(words[:2]) if words else kw["title"].split()[0]

            pos = await _find_position(search_term, kw["id"])
            emoji = "🥇" if 0 < pos <= 3 else "🥈" if pos <= 10 else "🥉" if pos <= 20 else "📍" if pos > 0 else "❌"
            pos_text = f"#{pos}" if pos > 0 else "не найден"
            results.append(f"{emoji} <b>{kw['title'][:50]}</b>\n   <code>{search_term}</code> → {pos_text}")
            await asyncio.sleep(2)

        return "\n".join(results)
    except Exception as e:
        log.error("Ошибка SEO: %s", e)
        return f"❌ Ошибка SEO: {e}"


async def _find_position(search_term: str, kwork_id: str) -> int:
    try:
        await state.page.goto(f"https://kwork.ru/search?query={search_term}", timeout=60_000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        return await state.page.evaluate(f"""() => {{
            const links = document.querySelectorAll('a[href*="/kwork/"]');
            let pos = 0;
            const seen = new Set();
            for (const link of links) {{
                const href = link.getAttribute('href') || '';
                if (!seen.has(href) && href.includes('/kwork/')) {{
                    seen.add(href);
                    pos++;
                    if (href.includes('/{kwork_id}')) return pos;
                }}
            }}
            return 0;
        }}""")
    except Exception:
        return 0
