"""Claude AI integratsiyasi."""
import asyncio
import json
import re
import logging

import anthropic

from app.core.config import CLAUDE_API_KEY, RESPONSE_PROMPT

log = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

FALLBACK = {
    "response_text": "Здравствуйте! Готов взяться за ваш проект. Имею опыт в данной сфере. Напишите, обсудим детали.",
    "suggested_price": "3000",
    "complexity": "средний",
    "estimated_days": "3",
}


async def generate_response(title: str, description: str, budget: str) -> dict:
    """Proektga mos taklif va narx generatsiya qiladi."""
    prompt = f"""{RESPONSE_PROMPT}

Вот текст заказа:
Название: {title}
Описание: {description}
Бюджет заказчика: {budget}
"""
    try:
        response = await asyncio.to_thread(
            client.messages.create,
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        log.error("Claude xato: %s", e)

    return FALLBACK.copy()
