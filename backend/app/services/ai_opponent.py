from __future__ import annotations

import asyncio
import json
import logging
import re
import time

import certifi
import httpx

from ..config import get_settings
from .scoring import difficulty_prompt, local_ai_reply, persona_prompt

logger = logging.getLogger(__name__)

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Cloudflare режет Python-urllib / пустой UA (error 1010), из‑за этого раньше
# все запросы падали и включался локальный сценарийный ответчик.
_GROQ_HEADERS_EXTRA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}
# Llama 3.x на free/developer уже нет. gpt-oss — production и быстрее preview Qwen.
# Qwen без reasoning, gpt-oss — hidden, иначе content пустой и включается заглушка.
# На Passenger async httpx часто молчит, поэтому вызов синхронный.
_GROQ_MODELS = (
    {
        "id": "openai/gpt-oss-20b",
        "extra": {"reasoning_effort": "low", "reasoning_format": "hidden"},
    },
    {"id": "qwen/qwen3.8-27b", "extra": {"reasoning_effort": "none"}},
)
_GROQ_TIMEOUT = 8.0
_GROQ_COOLDOWN_SEC = 180.0
_POLLINATIONS_URL = "https://text.pollinations.ai/openai"
# openai-fast (nano) заметно быстрее дефолтного openai / gpt-5-mini.
_POLLINATIONS_MODELS = ("openai-fast",)
_POLLINATIONS_TIMEOUT = 18.0

last_groq_ok = False
last_groq_error: str | None = None
last_llm_provider: str | None = None
_groq_skip_until = 0.0
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


def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        **_GROQ_HEADERS_EXTRA,
    }


def _groq_on_cooldown() -> bool:
    return time.monotonic() < _groq_skip_until


def _set_groq_cooldown() -> None:
    global _groq_skip_until
    _groq_skip_until = time.monotonic() + _GROQ_COOLDOWN_SEC


def _clear_groq_cooldown() -> None:
    global _groq_skip_until
    _groq_skip_until = 0.0


def _is_auth_block(status_code: int, body: str) -> bool:
    if status_code in {401, 403}:
        return True
    lowered = (body or "").lower()
    return "forbidden" in lowered or "permission" in lowered


def _groq_chat_sync(
    messages: list[dict],
    *,
    temperature: float,
    max_tokens: int,
    reject_meta: bool = True,
) -> str | None:
    global last_groq_ok, last_groq_error, last_llm_provider
    if _groq_on_cooldown():
        return None
    settings = get_settings()
    key = (settings.groq_api_key or "").strip().strip('"').strip("'")
    if not key:
        last_groq_ok = False
        last_groq_error = "GROQ_API_KEY пуст"
        return None
    errors: list[str] = []
    try:
        with httpx.Client(timeout=_GROQ_TIMEOUT, verify=certifi.where()) as client:
            for spec in _GROQ_MODELS:
                try:
                    payload = {
                        "model": spec["id"],
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                    payload.update(spec.get("extra") or {})
                    resp = client.post(
                        _GROQ_URL,
                        headers={
                            "Authorization": f"Bearer {key}",
                            **_headers(),
                        },
                        json=payload,
                    )
                    if resp.status_code >= 400:
                        detail = (resp.text or "").replace("\n", " ").strip()[:180]
                        err = f"{spec['id']}: HTTP {resp.status_code} {detail}".strip()
                        errors.append(err)
                        logger.warning("Groq %s", err)
                        if _is_auth_block(resp.status_code, detail):
                            break
                        continue
                    text = _extract_chat_text(resp.json())
                    if not text:
                        errors.append(f"{spec['id']}: пустой ответ")
                        continue
                    if reject_meta and _looks_like_meta_reply(text):
                        errors.append(f"{spec['id']}: отклонён как meta")
                        continue
                    last_groq_ok = True
                    last_groq_error = None
                    last_llm_provider = f"groq:{spec['id']}"
                    _clear_groq_cooldown()
                    return text
                except Exception as exc:
                    err = f"{spec['id']}: {type(exc).__name__}: {exc}"[:180]
                    errors.append(err)
                    logger.warning("Groq request failed: %s", err)
                    continue
    except Exception as exc:
        last_groq_ok = False
        last_groq_error = type(exc).__name__
        logger.warning("Groq client failed: %s", last_groq_error)
        return None
    last_groq_ok = False
    last_groq_error = " | ".join(errors) if errors else "ни одна модель не ответила"
    if any(_is_auth_block(403, err) or "HTTP 401" in err or "HTTP 403" in err for err in errors):
        _set_groq_cooldown()
    return None


def _pollinations_chat_sync(
    messages: list[dict],
    *,
    temperature: float,
    max_tokens: int,
    reject_meta: bool = True,
) -> str | None:
    global last_llm_provider
    try:
        with httpx.Client(timeout=_POLLINATIONS_TIMEOUT, verify=certifi.where()) as client:
            for model in _POLLINATIONS_MODELS:
                try:
                    resp = client.post(
                        _POLLINATIONS_URL,
                        headers=_headers(),
                        json={
                            "model": model,
                            "messages": messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            "reasoning_effort": "low",
                            "reasoning_format": "hidden",
                        },
                    )
                    if resp.status_code >= 400:
                        detail = (resp.text or "").replace("\n", " ").strip()[:180]
                        logger.warning("Pollinations %s HTTP %s %s", model, resp.status_code, detail)
                        continue
                    text = _extract_chat_text(resp.json())
                    if not text:
                        continue
                    if reject_meta and _looks_like_meta_reply(text):
                        continue
                    last_llm_provider = f"pollinations:{model}"
                    return text
                except Exception as exc:
                    logger.warning("Pollinations %s failed: %s", model, type(exc).__name__)
                    continue
    except Exception as exc:
        logger.warning("Pollinations failed: %s", type(exc).__name__)
        return None
    return None


def _llm_chat_sync(
    messages: list[dict],
    *,
    temperature: float,
    max_tokens: int,
    reject_meta: bool = True,
    allow_pollinations: bool = True,
) -> str | None:
    text = _groq_chat_sync(
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        reject_meta=reject_meta,
    )
    if text:
        return text
    if not allow_pollinations:
        return None
    return _pollinations_chat_sync(
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        reject_meta=reject_meta,
    )


def probe_llm() -> str | None:
    """Короткий пинг для /api/health?probe=1."""
    return _llm_chat_sync(
        [{"role": "user", "content": "Ответь одним словом: ок"}],
        temperature=0.0,
        max_tokens=16,
        reject_meta=False,
    )


async def _llm_chat(
    messages: list[dict],
    *,
    temperature: float,
    max_tokens: int,
    reject_meta: bool = True,
    allow_pollinations: bool = True,
) -> str | None:
    return await asyncio.to_thread(
        _llm_chat_sync,
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        reject_meta=reject_meta,
        allow_pollinations=allow_pollinations,
    )


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
    if _groq_on_cooldown() or (not last_groq_ok and last_groq_error):
        return local_is_on_topic(scenario, user_text, history)
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
    raw = await _llm_chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.0,
        max_tokens=40,
        reject_meta=False,
        allow_pollinations=False,
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
    Бесплатный LLM: Groq → Pollinations → локальный сценарийный ответчик.
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

    groq_text = await _llm_chat(
        messages,
        temperature=0.7 if difficulty != "hard" else 0.85,
        max_tokens=220,
    )
    if groq_text and not _looks_like_meta_reply(groq_text):
        return groq_text

    return local_ai_reply(scenario, difficulty, history, user_text or "Начнём переговоры.")
