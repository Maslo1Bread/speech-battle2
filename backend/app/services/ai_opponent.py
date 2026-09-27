from __future__ import annotations

import httpx

from ..config import get_settings
from .scoring import difficulty_prompt, local_ai_reply


async def generate_ai_reply(
    scenario: dict,
    difficulty: str,
    history: list[dict],
    user_text: str | None = None,
) -> str:
    """
    Бесплатный LLM: Groq (если есть ключ) → иначе локальный сценарийный ответчик.
    Groq free tier: https://console.groq.com
    """
    settings = get_settings()
    system = (
        "Ты оппонент в симуляторе деловых переговоров «Арена переговоров». "
        "Отвечай только по роли и только в рамках сценария. "
        "Пиши коротко (2–5 предложений), по-русски, без markdown.\n"
        f"Сценарий: {scenario.get('name')}\n"
        f"Контекст: {scenario.get('context')}\n"
        f"Твоя роль: {scenario.get('opponent_role')}\n"
        f"Твои цели: {', '.join(scenario.get('goals_opponent', []))}\n"
        f"Роль игрока: {scenario.get('player_role')}\n"
        f"{difficulty_prompt(difficulty)}"
    )

    messages = [{"role": "system", "content": system}]
    for item in history[-12:]:
        role = "assistant" if item.get("sender_type") == "ai" else "user"
        messages.append({"role": role, "content": item["content"]})
    if user_text:
        messages.append({"role": "user", "content": user_text})

    if settings.groq_api_key:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.groq_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        # Актуальная бесплатная chat-модель Groq (llama-3.1 снята)
                        "model": "openai/gpt-oss-20b",
                        "messages": messages,
                        "temperature": 0.7 if difficulty != "hard" else 0.85,
                        "max_tokens": 280,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                text = (data["choices"][0]["message"].get("content") or "").strip()
                if text:
                    return text
        except Exception:
            pass

    # Полностью бесплатный запасной путь без ключей
    return local_ai_reply(scenario, difficulty, history, user_text or "Начнём переговоры.")
