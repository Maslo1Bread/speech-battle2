#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Настройка русской клавиатуры на Android эмуляторах
# Использование: bash scripts/setup_russian_keyboard.sh
# ─────────────────────────────────────────────────────────────────

ADB=~/Library/Android/sdk/platform-tools/adb

echo "🔧 Настройка русской клавиатуры на всех эмуляторах..."

# Получаем список всех подключённых устройств
DEVICES=$($ADB devices | grep emulator | awk '{print $1}')

if [ -z "$DEVICES" ]; then
    echo "❌ Нет запущенных эмуляторов"
    echo "💡 Запустите эмулятор: ~/Library/Android/sdk/emulator/emulator -avd Pixel_10_Pro &"
    exit 1
fi

for DEVICE in $DEVICES; do
    echo ""
    echo "📱 Настройка устройства: $DEVICE"
    
    # 1. Добавляем русский язык в систему
    echo "  → Добавляем русский язык в систему..."
    $ADB -s $DEVICE shell "settings put system system_locales ru-RU"
    
    # 2. Включаем Google Keyboard
    echo "  → Включаем Google Keyboard..."
    $ADB -s $DEVICE shell "ime enable com.google.android.inputmethod.latin/com.android.inputmethod.latin.LatinIME" 2>/dev/null
    
    # 3. Устанавливаем Google Keyboard как основную
    echo "  → Устанавливаем Google Keyboard как основную..."
    $ADB -s $DEVICE shell "settings put secure default_input_method com.google.android.inputmethod.latin/com.android.inputmethod.latin.LatinIME"
    
    # 4. Добавляем русский язык в клавиатуру (subtype ID для русского: -921088104)
    echo "  → Добавляем русский язык в клавиатуру..."
    $ADB -s $DEVICE shell "settings put secure selected_input_method_subtypes -921088104"
    
    # 5. Устанавливаем активный subtype
    echo "  → Устанавливаем русский как активный язык..."
    $ADB -s $DEVICE shell "settings put secure selected_input_method_subtype 1594443099"
    
    # 6. Добавляем русский в историю языков
    echo "  → Добавляем русский в историю языков..."
    $ADB -s $DEVICE shell "settings put secure input_methods_subtype_history com.google.android.inputmethod.latin/com.android.inputmethod.latin.LatinIME;-921088104"
    
    # 7. Обновляем enabled_input_methods
    echo "  → Обновляем список включённых методов ввода..."
    $ADB -s $DEVICE shell "settings put secure enabled_input_methods com.google.android.inputmethod.latin/com.android.inputmethod.latin.LatinIME;-921088104:com.google.android.tts/com.google.android.apps.speech.tts.googletts.settings.asr.voiceime.VoiceInputMethodService"
    
    echo "  ✅ Русская клавиатура настроена на $DEVICE"
done

echo ""
echo "✅ Настройка завершена!"
echo ""
echo "📋 Проверка настройки:"
for DEVICE in $DEVICES; do
    echo ""
    echo "📱 Устройство: $DEVICE"
    echo "  Локаль: $($ADB -s $DEVICE shell "settings get system system_locales" | tr -d '\r')"
    echo "  Клавиатура: $($ADB -s $DEVICE shell "settings get secure default_input_method" | tr -d '\r')"
    echo "  Русский subtype: $($ADB -s $DEVICE shell "settings get secure selected_input_method_subtypes" | tr -d '\r')"
done

echo ""
echo "💡 Для переключения языка на клавиатуре:"
echo "   1. Нажмите на поле ввода"
echo "   2. Нажмите на иконку клавиатуры в нижней панели"
echo "   3. Выберите 'Русский' или нажмите на глобус/пробел"
echo ""
echo "🔄 Если клавиатура не переключается, перезапустите приложение"
