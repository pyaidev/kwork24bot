"""Playwright brauzer boshqaruvi."""
import json
import logging

from playwright.async_api import async_playwright

from app.core.config import COOKIES_FILE
from app.core import state
from app.services.human import BROWSER_INIT_SCRIPT

log = logging.getLogger(__name__)

pw_instance = None
browser_instance = None


async def setup():
    """Brauzerni ishga tushiradi va cookie yuklaydi."""
    global pw_instance, browser_instance

    if browser_instance:
        try:
            await browser_instance.close()
        except Exception:
            pass
    if pw_instance:
        try:
            await pw_instance.stop()
        except Exception:
            pass

    pw_instance = await async_playwright().start()
    browser_instance = await pw_instance.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
        ],
    )
    state.browser_context = await browser_instance.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        extra_http_headers={"Accept-Language": "ru-RU,ru;q=0.9"},
    )
    await state.browser_context.add_init_script(BROWSER_INIT_SCRIPT)

    if not await load_cookies(state.browser_context):
        log.error("Cookie yuklash xatosi!")
        return False

    state.page = await state.browser_context.new_page()

    import asyncio
    await state.page.goto("https://kwork.ru/settings", timeout=60_000, wait_until="domcontentloaded")
    await asyncio.sleep(3)
    if "login" in state.page.url:
        log.error("Cookie eskirgan!")
        return False

    state.browser = browser_instance
    log.info("Brauzer tayyor ✓")
    return True


async def load_cookies(context):
    try:
        with open(COOKIES_FILE, "r") as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        return True
    except Exception as e:
        log.error("Cookie xato: %s", e)
        return False


async def save_cookies():
    """Cookie larni faylga saqlaydi."""
    if not state.browser_context:
        return
    try:
        cookies = await state.browser_context.cookies()
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f, indent=2)
        state.stats["cookie_refreshes"] += 1
        log.info("Cookie saqlandi: %d ta", len(cookies))
    except Exception as e:
        log.error("Cookie saqlash xato: %s", e)
