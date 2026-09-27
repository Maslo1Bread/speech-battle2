#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Проверка статуса русской клавиатуры на эмуляторах
# ─────────────────────────────────────────────────────────────────

ADB=~/Library/Android/sdk/platform-tools/adb

echo "🔍 Проверка статуса русской клавиатуры"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Получаем список всех подключённых устройств
DEVICES=$($ADB devices | grep emulator | awk '{print $1}')

if [ -z "$DEVICES" ]; then
    echo "❌ Нет запущенных эмуляторов"
    exit 1
fi

for DEVICE in $DEVICES; do
    echo "📱 Устройство: $DEVICE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Системная локаль
    LOCALE=$($ADB -s $DEVICE shell "settings get system system_locales" | tr -d '\r')
    echo "  🌍 Системная локаль: ${LOCALE:-не установлена}"
    
    # Текущая клавиатура
    KEYBOARD=$($ADB -s $DEVICE shell "settings get secure default_input_method" | tr -d '\r')
    echo "  ⌨️  Клавиатура: ${KEYBOARD:-не установлена}"
    
    # Активный subtype (язык)
    SUBTYPE=$($ADB -s $DEVICE shell "settings get secure selected_input_method_subtype" | tr -d '\r')
    if [ "$SUBTYPE" = "1594443099" ]; then
        echo "  🔤 Активный язык: Русский ✅"
    else
        echo "  🔤 Активный язык: Не русский (subtype: $SUBTYPE)"
    fi
    
    # Русский subtype в настройках
    RU_SUBTYPE=$($ADB -s $DEVICE shell "settings get secure selected_input_method_subtypes" | tr -d '\r')
    if [ "$RU_SUBTYPE" = "-921088104" ]; then
        echo "  📋 Русский в списке: Да ✅"
    else
        echo "  📋 Русский в списке: Нет или не определено"
    fi
    
    # Список всех клавиатур
    echo "  📝 Доступные клавиатуры:"
    $ADB -s $DEVICE shell "ime list -s" | while read line; do
        echo "     • $line"
    done
    
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Как переключить клавиатуру на русский:"
echo "  1. Нажмите на текстовое поле"
echo "  2. Проведите вниз от верха экрана"
echo "  3. Нажмите 'Choose keyboard' или 'Выбрать клавиатуру'"
echo "  4. Выберите 'Русский'"
echo ""
echo "🔧 Или выполните команду:"
echo "  ~/Library/Android/sdk/platform-tools/adb shell am start -a android.settings.INPUT_METHOD_SETTINGS"
