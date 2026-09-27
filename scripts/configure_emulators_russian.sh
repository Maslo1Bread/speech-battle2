#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Постоянная настройка русской локали в конфигурации эмуляторов
# ─────────────────────────────────────────────────────────────────

echo "🔧 Настройка русской локали в конфигурации эмуляторов..."

# Список эмуляторов
EMULATORS=("Pixel_10_Pro" "SpeechPhone")

for EMU in "${EMULATORS[@]}"; do
    CONFIG_FILE="$HOME/.android/avd/${EMU}.avd/config.ini"
    
    if [ -f "$CONFIG_FILE" ]; then
        echo ""
        echo "📱 Настройка эмулятора: $EMU"
        
        # Проверяем, есть ли уже настройка локали
        if grep -q "hw.locale" "$CONFIG_FILE"; then
            echo "  → Обновляем существующую локаль..."
            # Удаляем старые настройки локали
            grep -v "hw.locale" "$CONFIG_FILE" > "${CONFIG_FILE}.tmp"
            mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
        fi
        
        # Добавляем русскую локаль
        echo "  → Добавляем русскую локаль (ru-RU)..."
        echo "" >> "$CONFIG_FILE"
        echo "# Russian locale configuration" >> "$CONFIG_FILE"
        echo "hw.locale.region=RU" >> "$CONFIG_FILE"
        echo "hw.locale.language=ru" >> "$CONFIG_FILE"
        
        echo "  ✅ Русская локаль добавлена в конфигурацию $EMU"
    else
        echo "  ⚠️  Конфигурационный файл не найден: $CONFIG_FILE"
    fi
done

echo ""
echo "✅ Настройка завершена!"
echo ""
echo "⚠️  Для применения изменений перезапустите эмуляторы:"
echo "   1. Закройте все эмуляторы"
echo "   2. Запустите эмулятор снова:"
echo "      ~/Library/Android/sdk/emulator/emulator -avd Pixel_10_Pro &"
echo "      ~/Library/Android/sdk/emulator/emulator -avd SpeechPhone &"
echo ""
echo "💡 После перезапуска запустите скрипт setup_russian_keyboard.sh"
