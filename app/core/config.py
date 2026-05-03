import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Kwork
COOKIES_FILE = os.getenv("COOKIES_FILE", "cookies.json")

# Claude AI
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# Intervallar (soniyada)
CHECK_PROJECTS_INTERVAL = 5 * 60
CHECK_INBOX_INTERVAL = 2 * 60
ONLINE_INTERVAL_MIN = 7 * 60
ONLINE_INTERVAL_MAX = 10 * 60
COOKIE_REFRESH_INTERVAL = 2 * 3600
SEO_CHECK_INTERVAL = 6 * 3600

# Monitoring kalit so'zlari
KEYWORDS = [
    "python", "django", "flask", "telegram bot", "телеграм бот",
    "парсинг", "парсер", "скрипт", "автоматизация", "бот",
    "api", "scraping", "fastapi", "aiogram", "selenium",
    "playwright", "backend", "бэкенд",
]

# Online tutish uchun sahifalar
ONLINE_PAGES = [
    "https://kwork.ru/projects?a=1",
    "https://kwork.ru/seller",
    "https://kwork.ru/inbox",
    "https://kwork.ru/my-kworks",
]

# Claude prompt
RESPONSE_PROMPT = """Напиши короткий, профессиональный отклик на фриланс-заказ на русском языке.

Требования к ответу:
— без воды, конкретно и по делу
— стиль уверенный, как у опытного разработчика
— не использовать сложные слова и перегруз
— не слишком длинный (5–10 строк)
— без списков и без лишнего форматирования
— писать так, будто я уже делал подобные проекты

В ответе обязательно:
— кратко показать, что задача понятна
— написать, как я буду реализовывать (в общих чертах)
— указать стек (если уместно: Python, Django, FastAPI, React и т.д.)
— упомянуть стабильность, масштабируемость
— добавить сроки и стоимость (примерно)
— закончить фразой "Готов обсудить детали"

ВАЖНО:
— не копируй текст задания
— не задавай вопросы
— не пиши шаблонно, делай как живой человек
— адаптируй ответ под конкретное ТЗ

Ответ верни в JSON формате:
{
    "response_text": "текст отклика",
    "suggested_price": "цена в рублях (только число)",
    "complexity": "легкий / средний / сложный",
    "estimated_days": "срок в днях (только число)"
}

Только JSON, больше ничего не пиши.
"""
