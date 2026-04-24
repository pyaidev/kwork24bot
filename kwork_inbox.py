import asyncio
import logging
import hashlib
import aiohttp
from playwright.async_api import async_playwright

# ========== SOZLAMALAR ==========
KWORK_LOGIN    = "pyaidev"
KWORK_PASSWORD = "Python111"

TELEGRAM_TOKEN = "8434156117:AAEMOpoOfPIeDbwDT_72RNRRlNCjSNBjaB0"
TELEGRAM_CHAT  = "8305515189"

CHECK_INTERVAL = 2 * 60   # har 2 daqiqa
# ================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# Oldingi holat: { username: message_hash }
prev_state: dict[str, str] = {}


def msg_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


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


async def login(page) -> bool:
    await page.goto("https://kwork.ru/login", timeout=60000, wait_until="domcontentloaded")
    await asyncio.sleep(3)
    await page.fill('input[placeholder="Электронная почта или логин"]', KWORK_LOGIN)
    await page.fill('input[type="password"]', KWORK_PASSWORD)
    await page.click('button:has-text("Войти")')
    await asyncio.sleep(6)
    ok = "login" not in page.url
    log.info("Login %s → %s", "OK" if ok else "XATO", page.url)
    return ok


async def get_inbox(page) -> list[dict]:
    """Inbox dan barcha suhbatlarni oladi."""
    await page.goto("https://kwork.ru/inbox", timeout=60000, wait_until="domcontentloaded")
    await asyncio.sleep(3)

    if "login" in page.url:
        return []

    data = await page.evaluate("""() => {
        const items = document.querySelectorAll('.chat__list-item');
        return Array.from(items).map(item => {
            const user = item.querySelector('.chat__list-user')?.innerText?.trim() || '';
            const msg  = item.querySelector('.chat__list-message')?.innerText?.trim() || '';
            const date = item.querySelector('.chat__list-date')?.innerText?.trim() || '';
            return { user, msg, date };
        }).filter(x => x.user);
    }""")
    return data


async def check_inbox(page):
    global prev_state

    convs = await get_inbox(page)
    log.info("Inbox: %d suhbat", len(convs))

    new_msgs = []

    for c in convs:
        user = c["user"]
        msg  = c["msg"]
        date = c["date"]

        # "Вы:" bilan boshlanuvchi xabarlar — o'zim yozganlar, skip
        if msg.startswith("Вы:"):
            prev_state[user] = msg_hash(msg)
            continue

        # Bo'sh xabar
        if not msg:
            continue

        current_hash = msg_hash(msg + date)
        prev_hash = prev_state.get(user)

        if prev_hash is None:
            # Birinchi ishga tushish — holatni saqla, notif yuborma
            prev_state[user] = current_hash
        elif prev_hash != current_hash:
            # Yangi xabar!
            prev_state[user] = current_hash
            new_msgs.append({
                "user": user,
                "msg": msg,
                "date": date,
                "url": f"https://kwork.ru/inbox/{user}",
            })

    for m in new_msgs:
        text = (
            f"💬 <b>Yangi xabar!</b>\n\n"
            f"👤 <b>{m['user']}</b>\n"
            f"🕐 {m['date']}\n\n"
            f"📩 {m['msg']}\n\n"
            f"🔗 <a href=\"{m['url']}\">Javob berish</a>"
        )
        await send_telegram(text)
        log.info("  → Xabar yuborildi: %s | %s", m['user'], m['msg'][:60])
        await asyncio.sleep(0.5)

    if not new_msgs:
        log.info("Yangi xabar yo'q")


async def main():
    log.info("Kwork Inbox Monitor ishga tushdi")
    log.info("Interval: %d daqiqa", CHECK_INTERVAL // 60)
    print("-" * 50)

    await send_telegram("📬 <b>Kwork Inbox Monitor ishga tushdi!</b>\n\nYangi xabarlar kelsa sizga darhol xabar beraman.")

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
            log.error("Login muvaffaqiyatsiz!")
            await browser.close()
            return

        # Birinchi tekshiruv — holatni yuklash (notif yubormasdan)
        log.info("Boshlang'ich holat yuklanmoqda...")
        await check_inbox(page)
        log.info("Tayyor. Monitoring boshlandi.")

        while True:
            log.info("Keyingi tekshiruv: %d daqiqadan keyin", CHECK_INTERVAL // 60)
            await asyncio.sleep(CHECK_INTERVAL)

            log.info("Inbox tekshirilmoqda...")
            try:
                await check_inbox(page)
            except Exception as e:
                log.error("Xato: %s", e)
                try:
                    await login(page)
                except Exception:
                    pass


if __name__ == "__main__":
    asyncio.run(main())
