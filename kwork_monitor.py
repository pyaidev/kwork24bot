import asyncio
import logging
import aiohttp
from playwright.async_api import async_playwright

# ========== SOZLAMALAR ==========
KWORK_LOGIN    = "pyaidev"
KWORK_PASSWORD = "Python111"

TELEGRAM_TOKEN  = "8434156117:AAEMOpoOfPIeDbwDT_72RNRRlNCjSNBjaB0"
TELEGRAM_CHAT   = "8305515189"

CHECK_INTERVAL  = 5 * 60   # har 5 daqiqa

SEARCH_URLS = [
    "https://kwork.ru/projects?keyword=django&a=1",
    "https://kwork.ru/projects?a=1&keyword=Python",
]
# ================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

seen_ids: set[str] = set()


async def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                body = await resp.text()
                log.error("Telegram xato: %s", body)


async def login(page):
    await page.goto("https://kwork.ru/login", timeout=60000, wait_until="domcontentloaded")
    await asyncio.sleep(3)
    await page.fill('input[placeholder="Электронная почта или логин"]', KWORK_LOGIN)
    await page.fill('input[type="password"]', KWORK_PASSWORD)
    await page.click('button:has-text("Войти")')
    await asyncio.sleep(6)
    if "login" not in page.url:
        log.info("Login OK → %s", page.url)
        return True
    log.error("Login xato!")
    return False


async def scrape_projects(page, url: str) -> list[dict]:
    await page.goto(url, timeout=60000, wait_until="domcontentloaded")
    await asyncio.sleep(3)

    # Login yo'qolgan bo'lsa qayta kirish
    if "login" in page.url:
        return []

    cards = await page.query_selector_all(".want-card")
    projects = []

    for card in cards:
        try:
            # ID va link
            link_el = await card.query_selector("h1 a, h2 a, .wants-card__header-title a")
            if not link_el:
                continue
            href = await link_el.get_attribute("href")
            if not href:
                continue
            project_id = href.strip("/").split("/")[-1]
            title = (await link_el.inner_text()).strip()

            # Tavsif
            desc_el = await card.query_selector(".wants-card__description-text .d-inline")
            desc = (await desc_el.inner_text()).strip()[:300] if desc_el else ""

            # Narx
            price_el = await card.query_selector(".wants-card__price")
            price = (await price_el.inner_text()).strip() if price_el else ""
            price = " ".join(price.split())

            # Vaqt qoldi
            time_el = await card.query_selector(".want-card__informers")
            time_text = (await time_el.inner_text()).strip() if time_el else ""
            time_text = " ".join(time_text.split())

            projects.append({
                "id": project_id,
                "title": title,
                "desc": desc,
                "price": price,
                "info": time_text,
                "url": f"https://kwork.ru{href}",
            })
        except Exception as e:
            log.warning("Card parse xato: %s", e)

    return projects


async def check_and_notify(page):
    new_count = 0
    for url in SEARCH_URLS:
        keyword = url.split("keyword=")[-1].split("&")[0]
        projects = await scrape_projects(page, url)
        log.info("[%s] %d proekt topildi", keyword, len(projects))

        for p in projects:
            if p["id"] in seen_ids:
                continue
            seen_ids.add(p["id"])

            msg = (
                f"🆕 <b>{p['title']}</b>\n\n"
                f"📝 {p['desc']}...\n\n"
                f"💰 {p['price']}\n"
                f"ℹ️ {p['info']}\n\n"
                f"🔍 Kalit so'z: <code>{keyword}</code>\n"
                f"🔗 <a href=\"{p['url']}\">Proektga o'tish</a>"
            )
            await send_telegram(msg)
            log.info("  → Yuborildi: [%s] %s", p['id'], p['title'])
            new_count += 1
            await asyncio.sleep(1)

    if new_count == 0:
        log.info("Yangi proekt yo'q")
    return new_count


async def main():
    log.info("Kwork Monitor ishga tushdi")
    log.info("Kuzatilayotgan: %s", [u.split("keyword=")[-1].split("&")[0] for u in SEARCH_URLS])
    log.info("Interval: %d daqiqa", CHECK_INTERVAL // 60)
    print("-" * 50)

    await send_telegram("✅ <b>Kwork Monitor ishga tushdi!</b>\n\nDjango va Python proektlarini kuzatyapman...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            extra_http_headers={"Accept-Language": "ru-RU,ru;q=0.9"},
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = await context.new_page()

        if not await login(page):
            log.error("Login muvaffaqiyatsiz. Chiqilmoqda.")
            await browser.close()
            return

        while True:
            log.info("Tekshirilmoqda...")
            try:
                await check_and_notify(page)
            except Exception as e:
                log.error("Xato: %s", e)
                # Session yangilash
                try:
                    await login(page)
                except Exception:
                    pass

            log.info("Keyingi tekshiruv: %d daqiqadan keyin", CHECK_INTERVAL // 60)
            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
