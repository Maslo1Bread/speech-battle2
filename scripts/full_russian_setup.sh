#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Полная настройка русской клавиатуры и локали для Speech-Battle
# ─────────────────────────────────────────────────────────────────

echo "🚀 Полная настройка русского языка для Speech-Battle"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ADB=~/Library/Android/sdk/platform-tools/adb
EMU=~/Library/Android/sdk/emulator/emulator

# 1. Настраиваем конфигурацию эмуляторов
echo "📝 Шаг 1: Настройка конфигурации эмуляторов..."
bash "$(dirname "$0")/configure_emulators_russian.sh"

echo ""
echo "📝 Шаг 2: Настройка русской клавиатуры на запущенных эмуляторах..."
bash "$(dirname "$0")/setup_russian_keyboard.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Настройка завершена!"
echo ""
echo "📱 Как использовать русскую клавиатуру:"
echo ""
echo "Способ 1: Через клавиатуру"
echo "  1. Нажмите на любое текстовое поле"
echo "  2. На клавиатуре нажмите на:"
echo "     • Глобус 🌐 (если есть)"
echo "  3. Или нажмите и удерживайте пробел"
echo "  4. Выберите 'Русский' из списка"
echo ""
echo "Способ 2: Через настройки"
echo "  1. На эмуляторе откройте Settings"
echo "  2. System → Languages → Keyboard"
echo "  3. Выберите 'Russian'"
echo ""
echo "Способ 3: Через ADB (если не работает)"
echo "  ~/Library/Android/sdk/platform-tools/adb shell am start -a android.settings.INPUT_METHOD_SETTINGS"
echo ""
echo "💡 Если клавиатура всё ещё на английском:"
echo "  1. Перезапустите эмулятор"
echo "  2. Запустите этот скрипт снова"
echo "  3. Откройте приложение Speech-Battle"
echo ""
