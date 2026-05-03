"""Background tasklar — monitoring looplari."""
import asyncio
import random
import logging

from app.core.config import (
    CHECK_PROJECTS_INTERVAL, CHECK_INBOX_INTERVAL,
    ONLINE_INTERVAL_MIN, ONLINE_INTERVAL_MAX,
    COOKIE_REFRESH_INTERVAL, SEO_CHECK_INTERVAL,
)
from app.core import state
from app.services import kwork, browser

log = logging.getLogger(__name__)


async def project_monitor_loop(notify_fn):
    while state.monitoring_active:
        await asyncio.sleep(CHECK_PROJECTS_INTERVAL)
        if not state.monitoring_active:
            break
        log.info("Proektlar tekshirilmoqda...")
        try:
            count = await kwork.check_all_projects(notify_fn)
            if count:
                log.info("%d ta yangi proekt", count)
        except Exception as e:
            state.stats["errors"] += 1
            log.error("Monitor xato: %s", e)


async def inbox_monitor_loop(notify_fn):
    while state.monitoring_active:
        await asyncio.sleep(CHECK_INBOX_INTERVAL)
        if not state.monitoring_active:
            break
        try:
            await kwork.check_inbox(notify_fn)
        except Exception as e:
            state.stats["errors"] += 1
            log.error("Inbox xato: %s", e)


async def online_loop():
    while state.monitoring_active:
        wait = random.randint(ONLINE_INTERVAL_MIN, ONLINE_INTERVAL_MAX)
        await asyncio.sleep(wait)
        if not state.monitoring_active:
            break
        try:
            await kwork.online_ping()
        except Exception as e:
            state.stats["errors"] += 1
            log.error("Online xato: %s", e)


async def cookie_refresh_loop(notify_fn):
    while state.monitoring_active:
        await asyncio.sleep(COOKIE_REFRESH_INTERVAL)
        if not state.monitoring_active:
            break
        log.info("Cookie yangilanmoqda...")
        try:
            if state.page:
                await state.page.goto("https://kwork.ru/settings", timeout=60_000, wait_until="domcontentloaded")
                await asyncio.sleep(3)
                if "login" in state.page.url:
                    await notify_fn("⚠️ Cookie eskirgan!")
                    continue
                await browser.save_cookies()
        except Exception as e:
            state.stats["errors"] += 1
            log.error("Cookie xato: %s", e)


async def seo_monitor_loop(notify_fn):
    while state.monitoring_active:
        await asyncio.sleep(SEO_CHECK_INTERVAL)
        if not state.monitoring_active:
            break
        try:
            result = await kwork.check_seo()
            await notify_fn(result)
        except Exception as e:
            state.stats["errors"] += 1
            log.error("SEO xato: %s", e)


def start_all(notify_fn):
    """Barcha background tasklarni ishga tushiradi."""
    asyncio.create_task(project_monitor_loop(notify_fn))
    asyncio.create_task(inbox_monitor_loop(notify_fn))
    asyncio.create_task(online_loop())
    asyncio.create_task(cookie_refresh_loop(notify_fn))
    asyncio.create_task(seo_monitor_loop(notify_fn))
