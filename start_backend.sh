#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Speech-Battle Backend — запуск одной командой
# Использование: bash start_backend.sh
# ─────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Создаём venv если не существует
if [ ! -f ".venv/bin/python" ]; then
  echo "🔧 Создаём виртуальное окружение..."
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip -q
  .venv/bin/pip install -r requirements.txt -q
  echo "✅ Зависимости установлены"
fi

# Проверяем, не занят ли порт
if lsof -i TCP:9201 -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "⚠️  Порт 9201 уже занят — бекенд уже запущен?"
  echo "   Проверь: curl http://127.0.0.1:9201/api/health"
  exit 0
fi

echo "🚀 Запускаем бекенд на http://0.0.0.0:9201 ..."
echo "   Android эмулятор → http://10.0.2.2:9201"
echo "   iOS симулятор    → http://127.0.0.1:9201"
echo "   Остановить: Ctrl+C"
echo ""

.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 9201 --reload
