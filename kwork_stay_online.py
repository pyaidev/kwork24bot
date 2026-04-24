import asyncio
import random
import logging
from playwright.async_api import async_playwright

# ╔══════════════════════════════════════════╗
# ║         KWORK BOT  —  SOZLAMALAR         ║
# ╚══════════════════════════════════════════╝

KWORK_LOGIN    = "pyaidev"
KWORK_PASSWORD = "Python111"

# Online tutish oraligi (daqiqada)
MIN_INTERVAL = 7 * 60
MAX_INTERVAL = 10 * 60

# ── Monitoring kalit so'zlari ──────────────
KEYWORDS = [
    "python",
    "django",
    "flask",
    "telegram bot",
    "парсинг",
]

# ── Javob shablonlari ──────────────────────
# (Har safar bittasi tasodifiy tanlanadi)
RESPONSE_TEMPLATES = [
    "Здравствуйте! Готов взяться за ваш проект. Напишите, обсудим детали и сроки.",
    "Добрый день! Опыт в данной сфере есть, готов помочь. Свяжитесь для обсуждения.",
    "Здравствуйте! Вижу ваш проект — могу выполнить качественно и в срок. Пишите!",
]

# ── Online tutish sahifalari ───────────────
PAGES = [
    "https://kwork.ru/projects?a=1",
    "https://kwork.ru/seller",
    "https://kwork.ru/inbox",
    "https://kwork.ru/projects?keyword=django&a=1",
    "https://kwork.ru/projects?keyword=python&a=1",
    "https://kwork.ru/my-kworks",
]

# ══════════════════════════════════════════

# Allaqachon javob berilgan proektlar (session davomida)
responded_ids: set[str] = set()

# Statistika
stats = {"online_visits": 0, "projects_found": 0, "responses_sent": 0, "errors": 0}


# ── Logging ───────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def banner():
    print("=" * 52)
    print("   KWORK BOT  |  Online + Javob Monitoring")
    print("=" * 52)
    print(f"  Login     : {KWORK_LOGIN}")
    print(f"  Kalit so'z: {', '.join(KEYWORDS)}")
    print(f"  Interval  : {MIN_INTERVAL//60}–{MAX_INTERVAL//60} daqiqa")
    print("=" * 52)


def print_stats():
    print("-" * 40)
    print(f"  Online tashrif : {stats['online_visits']}")
    print(f"  Proekt topildi : {stats['projects_found']}")
    print(f"  Javob yuborildi: {stats['responses_sent']}")
    print(f"  Xatolar        : {stats['errors']}")
    print("-" * 40)


# ── Login ─────────────────────────────────
async def login(page) -> bool:
    log.info("Login qilinmoqda...")
    await page.goto("https://kwork.ru/login", timeout=60_000, wait_until="domcontentloaded")
    await asyncio.sleep(3)
    await page.fill('input[placeholder="Электронная почта или логин"]', KWORK_LOGIN)
    await page.fill('input[type="password"]', KWORK_PASSWORD)
    await page.click('button:has-text("Войти")')
    await asyncio.sleep(6)
    ok = "login" not in page.url
    log.info("Login: %s", "OK ✓" if ok else "XATO ✗")
    return ok


# ── Online tutish ─────────────────────────
async def visit_page(page, url: str) -> bool:
    try:
        await page.goto(url, timeout=60_000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        scroll = random.randint(300, 800)
        await page.evaluate(f"window.scrollBy(0, {scroll})")
        await asyncio.sleep(random.uniform(2, 4))
        stats["online_visits"] += 1
        log.info("Tashrif: %s", url)
        return True
    except Exception as e:
        stats["errors"] += 1
        log.warning("Xato [%s]: %s", url, e)
        return False


# ── Proekt monitoring ─────────────────────
async def check_projects(page, keyword: str):
    url = f"https://kwork.ru/projects?keyword={keyword}"
    log.info("Monitoring: '%s' so'zi bo'yicha proektlar tekshirilmoqda...", keyword)

    try:
        await page.goto(url, timeout=60_000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Proekt kartlarini topish
        cards = await page.query_selector_all(".wants-card, .card-item, [class*='project']")

        if not cards:
            log.info("  '%s' uchun proekt topilmadi.", keyword)
            return

        log.info("  %d ta proekt topildi.", len(cards))
        stats["projects_found"] += len(cards)

        for card in cards[:5]:  # Har safar max 5 ta
            try:
                link_el = await card.query_selector("a[href*='/projects/']")
                if not link_el:
                    continue

                href = await link_el.get_attribute("href")
                if not href:
                    continue

                # To'liq URL
                if href.startswith("/"):
                    href = "https://kwork.ru" + href

                # Proekt ID sini olish
                project_id = href.rstrip("/").split("/")[-2] + "_" + href.rstrip("/").split("/")[-1]

                if project_id in responded_ids:
                    continue  # Allaqachon javob berilgan

                # Proektga kirib javob yuborish
                sent = await respond_to_project(page, href, project_id)
                if sent:
                    responded_ids.add(project_id)

                await asyncio.sleep(random.uniform(3, 6))

            except Exception as e:
                log.warning("  Karta xato: %s", e)

    except Exception as e:
        stats["errors"] += 1
        log.warning("Monitoring xato [%s]: %s", keyword, e)


# ── Proektga javob yuborish ───────────────
async def respond_to_project(page, url: str, project_id: str) -> bool:
    try:
        await page.goto(url, timeout=60_000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # "Откликнуться" tugmasini topish
        btn = await page.query_selector(
            'button:has-text("Откликнуться"), '
            'a:has-text("Откликнуться"), '
            '[class*="want-btn"], [class*="respond"]'
        )

        if not btn:
            log.info("  [%s] Javob tugmasi topilmadi (allaqachon yopiqligi mumkin)", project_id)
            return False

        await btn.click()
        await asyncio.sleep(2)

        # Matn maydonini topish
        textarea = await page.query_selector(
            'textarea[placeholder*="опишите"], textarea[name*="message"], '
            'textarea[class*="form"], div[contenteditable="true"]'
        )

        if not textarea:
            log.warning("  [%s] Matn maydoni topilmadi", project_id)
            return False

        text = random.choice(RESPONSE_TEMPLATES)
        await textarea.fill(text)
        await asyncio.sleep(random.uniform(1, 2))

        # Yuborish tugmasi
        send_btn = await page.query_selector(
            'button:has-text("Отправить"), button:has-text("Откликнуться"), '
            'button[type="submit"]'
        )
        if send_btn:
            await send_btn.click()
            await asyncio.sleep(2)
            stats["responses_sent"] += 1
            log.info("  [%s] Javob yuborildi ✓", project_id)
            return True

    except Exception as e:
        stats["errors"] += 1
        log.warning("  Javob xato [%s]: %s", project_id, e)

    return False


# ── Asosiy tsikl ──────────────────────────
async def main():
    banner()

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
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            extra_http_headers={"Accept-Language": "ru-RU,ru;q=0.9"},
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = await context.new_page()

        if not await login(page):
            log.error("Login muvaffaqiyatsiz! Akkaunt yoki parolni tekshiring.")
            await browser.close()
            return

        page_index = 0
        cycle = 0

        while True:
            cycle += 1
            log.info("── Tsikl #%d ──────────────────────────", cycle)

            # 1) Online tutish — bir sahifani ko'rish
            url = PAGES[page_index % len(PAGES)]
            page_index += 1
            ok = await visit_page(page, url)

            # Session tekshirish
            if not ok or "login" in page.url:
                log.warning("Session tugagan, qayta login...")
                await login(page)

            # 2) Har 3 tsiklda bir — proektlarni monitoring qilish
            if cycle % 3 == 0:
                for kw in KEYWORDS:
                    await check_projects(page, kw)
                    await asyncio.sleep(random.uniform(5, 10))
                print_stats()

            # 3) Keyingi tsiklgacha kutish
            wait = random.randint(MIN_INTERVAL, MAX_INTERVAL)
            log.info("Keyingi tsikl: %d:%02d dan keyin", wait // 60, wait % 60)
            await asyncio.sleep(wait)


if __name__ == "__main__":
    asyncio.run(main())
