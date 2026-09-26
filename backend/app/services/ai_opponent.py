from __future__ import annotations

import json
import re

import httpx

from ..config import get_settings
from .scoring import difficulty_prompt, local_ai_reply, persona_prompt

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Llama 3.1/3.3 на Groq сняты. Бесплатный каталог: Qwen и GPT-OSS.
_GROQ_MODELS = (
    {"id": "qwen/qwen3.8-27b", "extra": {"reasoning_effort": "none"}},
    {
        "id": "openai/gpt-oss-20b",
        "extra": {"reasoning_effort": "low", "reasoning_format": "hidden"},
    },
)
_META_REPLY_MARKERS = (
    "в рамках сценария",
    "вы сказали:",
    "вы сказали «",
    "симулятор",
    "как ии",
    "я нейросеть",
    "я языковая модель",
    "игнорировать свои ограничения",
    "роль оппонента",
    "chatgpt",
    "gpt-oss",
    "we need to",
    "we are the",
    "we are chatgpt",
    "the user is",
    "instructions say",
    "respond as",
    "as the client",
    "as the manager",
    "so we are",
    "but we are",
    "wait, instructions",
    "the user says",
)

_NEGOTIATION_MARKERS = (
    "скидк",
    "цен",
    "стоим",
    "договор",
    "контракт",
    "бюджет",
    "услов",
    "срок",
    "оплат",
    "процент",
    "предлож",
    "соглас",
    "отказ",
    "марж",
    "клиент",
    "зарплат",
    "оклад",
    "повыш",
    "поставщик",
    "закуп",
    "услуг",
    "сделк",
    "компромисс",
    "встречн",
    "пакет",
    "бонус",
    "подпис",
    "деньг",
    "ставк",
    "обязан",
    "льгот",
    "гарант",
    "штраф",
    "ндс",
    "оффер",
    "оферт",
    "переговор",
)

_GREETINGS = (
    "здравств",
    "добрый",
    "привет",
    "доброго",
    "рад знаком",
    "начн",
    "давайте обсуд",
    "давай обсуд",
)

_OFFTOPIC_MARKERS = (
    "погод",
    "анекдот",
    "рецепт",
    "футбол",
    "хоккей",
    "minecraft",
    "фильм",
    "сериал",
    "мем",
    "гороскоп",
    "курс доллара",
    "крипт",
    "что поесть",
    "как дела",
    "кто президент",
)


def off_topic_warning(scenario: dict | None) -> str:
    title = (scenario or {}).get("name") or "текущий сценарий"
    return (
        f"Сообщение не по теме переговоров «{title}». "
        "Напишите реплику в рамках выбранного сценария — иначе оппонент не ответит."
    )


def _scenario_blob(scenario: dict) -> str:
    parts = [
        scenario.get("name", ""),
        scenario.get("desc", ""),
        scenario.get("context", ""),
        scenario.get("player_role", ""),
        scenario.get("opponent_role", ""),
        " ".join(scenario.get("goals_player", []) or []),
        " ".join(scenario.get("goals_opponent", []) or []),
    ]
    return " ".join(parts).lower()


def local_is_on_topic(scenario: dict, user_text: str, history: list[dict] | None = None) -> bool:
    """Запасной классификатор без API: false только для явно посторонних реплик."""
    text = (user_text or "").strip().lower()
    if len(text) < 2:
        return False
    if any(marker in text for marker in _OFFTOPIC_MARKERS) and not any(
        marker in text for marker in _NEGOTIATION_MARKERS
    ):
        return False
    if any(marker in text for marker in _NEGOTIATION_MARKERS):
        return True
    if any(g in text for g in _GREETINGS):
        return True
    blob = _scenario_blob(scenario)
    keywords = {w for w in re.findall(r"[а-яёa-z]{5,}", blob)}
    if any(word in text for word in keywords):
        return True
    if history:
        return True
    return len(text.split()) >= 6


def _extract_chat_text(data: dict) -> str:
    """Только готовая реплика. Поле reasoning и think-блоки не показываем."""
    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        return ""
    text = (message.get("content") or "").strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"</?think>", "", text, flags=re.IGNORECASE)
    return text.strip()


def _mostly_english(text: str) -> bool:
    latin = len(re.findall(r"[A-Za-z]{3,}", text or ""))
    cyrillic = len(re.findall(r"[А-Яа-яЁё]{3,}", text or ""))
    return latin >= 6 and latin > cyrillic


def _looks_like_meta_reply(text: str) -> bool:
    lowered = (text or "").lower()
    if any(marker in lowered for marker in _META_REPLY_MARKERS):
        return True
    return _mostly_english(text)


async def _groq_chat(
    messages: list[dict],
    *,
    temperature: float,
    max_tokens: int,
    reject_meta: bool = True,
) -> str | None:
    settings = get_settings()
    if not settings.groq_api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=40.0) as client:
            for spec in _GROQ_MODELS:
                try:
                    payload = {
                        "model": spec["id"],
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                    payload.update(spec.get("extra") or {})
                    resp = await client.post(
                        _GROQ_URL,
                        headers={
                            "Authorization": f"Bearer {settings.groq_api_key}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                    if resp.status_code >= 400:
                        continue
                    text = _extract_chat_text(resp.json())
                    if not text:
                        continue
                    if reject_meta and _looks_like_meta_reply(text):
                        continue
                    return text
                except Exception:
                    continue
    except Exception:
        return None
    return None


def _parse_on_topic(raw: str) -> bool | None:
    if not raw:
        return None
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    payload = match.group(0) if match else raw
    try:
        data = json.loads(payload)
        if "on_topic" in data:
            return bool(data["on_topic"])
    except Exception:
        pass
    lowered = raw.lower()
    if "false" in lowered and "true" not in lowered:
        return False
    if re.search(r"\bon_topic\b.*\btrue\b", lowered):
        return True
    if re.search(r"\bon_topic\b.*\bfalse\b", lowered):
        return False
    return None


async def is_on_topic(
    scenario: dict,
    user_text: str,
    history: list[dict] | None = None,
) -> bool:
    """True, если реплика хоть как-то относится к сценарию переговоров."""
    system = (
        "Ты фильтр темы в симуляторе деловых переговоров. "
        "Нужно понять, относится ли реплика пользователя к текущему сценарию. "
        "Верни ТОЛЬКО JSON вида {\"on_topic\": true} или {\"on_topic\": false}. "
        "on_topic=true, если есть любая связь со сделкой, ценой, условиями, ролями, "
        "аргументами, приветствием на встрече или продолжением диалога. "
        "on_topic=false ТОЛЬКО если сообщение совсем не в тему "
        "(погода, шутки, другая сфера, бессмысленный набор, просьба сменить тему)."
    )
    user = (
        f"Сценарий: {scenario.get('name')}\n"
        f"Описание: {scenario.get('desc')}\n"
        f"Контекст: {scenario.get('context')}\n"
        f"Роль игрока: {scenario.get('player_role')}\n"
        f"Роль оппонента: {scenario.get('opponent_role')}\n"
        f"Сообщение пользователя: {user_text}"
    )
    raw = await _groq_chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.0,
        max_tokens=40,
        reject_meta=False,
    )
    parsed = _parse_on_topic(raw or "")
    if parsed is not None:
        return parsed
    return local_is_on_topic(scenario, user_text, history)


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
    system = (
        "Ответ — только реплика на русском от первого лица, 2–5 коротких предложений. "
        "Никаких рассуждений, английского, списков, markdown, цитат собеседника, слов "
        "«сценарий», «симулятор», «роль», «инструкция», «ChatGPT», «ИИ».\n"
        f"{persona_prompt(scenario)}\n"
        f"Контекст встречи: {scenario.get('context')}\n"
        f"Твоя должность: {scenario.get('opponent_role')}. "
        f"Твои цели: {', '.join(scenario.get('goals_opponent', []))}.\n"
        f"Напротив тебя: {scenario.get('player_role')}. Отвечай ему как живому человеку на встрече.\n"
        f"{difficulty_prompt(difficulty)}"
    )

    messages = [{"role": "system", "content": system}]
    for item in history[-12:]:
        role = "assistant" if item.get("sender_type") == "ai" else "user"
        messages.append({"role": role, "content": item["content"]})
    if user_text:
        messages.append({"role": "user", "content": user_text})

    groq_text = await _groq_chat(
        messages,
        temperature=0.7 if difficulty != "hard" else 0.85,
        max_tokens=400,
    )
    if groq_text and not _looks_like_meta_reply(groq_text):
        return groq_text

    return local_ai_reply(scenario, difficulty, history, user_text or "Начнём переговоры.")
