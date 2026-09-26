from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

SCENARIOS_DIR = Path(__file__).resolve().parents[2] / "scenarios"

LOCKED_SCENARIOS = [
    {"id": "team-conflict", "name": "Конфликт в команде", "desc": "Медиация между двумя сотрудниками"},
    {"id": "investor-pitch", "name": "Разговор с инвестором", "desc": "Защита оценки и условий сделки"},
    {"id": "rent-renewal", "name": "Продление аренды", "desc": "Переговоры о ставке и условиях офиса"},
    {"id": "partnership", "name": "Партнёрское соглашение", "desc": "Раздел зон ответственности и прибыли"},
    {"id": "layoff-talk", "name": "Сложная кадровая беседа", "desc": "Сообщение о сокращении с сохранением уважения"},
    {"id": "deadline-push", "name": "Сдвиг дедлайна", "desc": "Клиент требует ускорить релиз без доплат"},
]


@lru_cache
def load_scenarios() -> dict[str, dict]:
    data: dict[str, dict] = {}
    for path in SCENARIOS_DIR.glob("*.json"):
        with path.open(encoding="utf-8") as fh:
            item = json.load(fh)
            data[item["id"]] = item
    return data


def list_scenarios_for_ui() -> list[dict]:
    available = []
    for item in load_scenarios().values():
        available.append(
            {
                "id": item["id"],
                "name": item["name"],
                "desc": item["desc"],
                "locked": False,
            }
        )
    # стабильный порядок: сначала доступные из файлов
    order = ["salary", "client-discount", "vendor-contract"]
    available.sort(key=lambda x: order.index(x["id"]) if x["id"] in order else 99)
    locked = [{**s, "locked": True} for s in LOCKED_SCENARIOS]
    return available + locked


def get_scenario(scenario_id: str) -> dict | None:
    return load_scenarios().get(scenario_id)
