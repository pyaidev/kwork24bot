import asyncio
import json
from playwright.async_api import async_playwright


async def main():
    print("Kwork cookie olish skripti")
    print("Brauzer ochiladi, login qiling...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        await page.goto("https://kwork.ru/login")

        print("\n>>> Brauzerda login qiling, keyin shu terminalga qaytib ENTER bosing...")
        input()

        cookies = await context.cookies()
        with open("cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)
        print(f"{len(cookies)} ta cookie saqlandi -> cookies.json")
        await browser.close()


asyncio.run(main())
