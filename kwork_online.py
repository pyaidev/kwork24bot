import asyncio
import random
import logging
from playwright.async_api import async_playwright

# ========== SOZLAMALAR ==========
EMAIL = "pyaidev"    # login yoki email
PASSWORD = "Python111"

MIN_INTERVAL = 3 * 60   # 3 daqiqa (soniyada)
MAX_INTERVAL = 4 * 60   # 4 daqiqa (soniyada)
# ================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


async def login(page):
    """Kwork.ru ga login qiladi. Muvaffaqiyatli bo'lsa True qaytaradi."""
    try:
        await page.goto("https://kwork.ru/login", timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=15000)

        # Login forma
        await page.fill('input[placeholder="Электронная почта или логин"]', EMAIL)
        await page.fill('input[type="password"]', PASSWORD)
        await page.click('button:has-text("Войти")')
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle", timeout=15000)

        # Login muvaffaqiyatli bo'lganini tekshirish
        url = page.url
        if "login" not in url:
            log.info("Login muvaffaqiyatli! URL: %s", url)
            return True
        else:
            log.error("Login muvaffaqiyatsiz! URL: %s", url)
            return False

    except Exception as e:
        log.error("Login xatosi: %s", e)
        return False


async def ping_kwork(page):
    """Akkaunt faol ekanligini tekshiradi yoki sahifani yangilaydi."""
    try:
        # Profil sahifasiga o'tib session ni yangilaydi
        await page.goto("https://kwork.ru/profile", timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=15000)

        url = page.url
        log.info("Ping OK  |  URL: %s", url)

        # Login sahifasiga redirect bo'lsa, session tugagan
        if "login" in url:
            log.warning("Session tugagan, qayta login qilinmoqda...")
            return False
        return True

    except Exception as e:
        log.error("Ping xatosi: %s", e)
        return False


async def main():
    log.info("Kwork Online Skript ishga tushdi")
    log.info("Email: %s", EMAIL)
    log.info("Interval: %d-%d daqiqa", MIN_INTERVAL // 60, MAX_INTERVAL // 60)
    print("-" * 50)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        # Birinchi marta login
        logged_in = await login(page)
        if not logged_in:
            log.error("Login qilishda xato. Email/parolni tekshiring.")
            await browser.close()
            return

        # Asosiy tsikl
        while True:
            wait = random.randint(MIN_INTERVAL, MAX_INTERVAL)
            log.info("Keyingi ping: %d soniyadan keyin (%d:%02d)", wait, wait // 60, wait % 60)
            await asyncio.sleep(wait)

            ok = await ping_kwork(page)
            if not ok:
                # Qayta login qilishga urinish
                logged_in = await login(page)
                if not logged_in:
                    log.error("Qayta login ham muvaffaqiyatsiz. 60 soniya kutilmoqda...")
                    await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
