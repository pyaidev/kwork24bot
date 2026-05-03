"""Inson xatti-harakatini simulatsiya qilish (anti-detection)."""
import asyncio
import random


async def human_fill(element, text: str):
    """Textarea ga inson kabi yozadi."""
    await element.click()
    await asyncio.sleep(random.uniform(0.3, 0.7))
    chunks = []
    i = 0
    while i < len(text):
        chunk_size = random.randint(3, 15)
        chunks.append(text[i:i + chunk_size])
        i += chunk_size
    for chunk in chunks:
        await element.type(chunk, delay=random.randint(30, 80))
        await asyncio.sleep(random.uniform(0.1, 0.4))
    await asyncio.sleep(random.uniform(0.5, 1.0))


async def human_scroll(page_obj):
    """Inson kabi sahifani scroll qiladi."""
    for _ in range(random.randint(2, 5)):
        await page_obj.evaluate(f"window.scrollBy(0, {random.randint(100, 500)})")
        await asyncio.sleep(random.uniform(0.5, 2.0))


async def human_pause():
    """Sahifani o'qish simulatsiyasi."""
    await asyncio.sleep(random.uniform(2, 6))


async def random_mouse_move(page_obj):
    """Sichqonchani random joyga siljitish."""
    x = random.randint(100, 900)
    y = random.randint(100, 600)
    await page_obj.mouse.move(x, y)
    await asyncio.sleep(random.uniform(0.3, 1.0))


BROWSER_INIT_SCRIPT = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    window.chrome = { runtime: {} };
    const origQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : origQuery(parameters);
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru', 'en-US', 'en'] });
    Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 4 });
"""
