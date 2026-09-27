#!/bin/bash
echo "Запуск Speech-Battle App"
echo "========================"

# Проверяем устройства
echo "Доступные устройства:"
flutter devices | grep -E "mobile|emulator"

echo ""
echo "Запускаем на первом Android устройстве..."
DEVICE=$(flutter devices | grep -E "android|emulator" | head -1 | awk '{print $1}')

if [ -z "$DEVICE" ]; then
    echo "Ошибка: Android устройство не найдено!"
    echo "Запустите эмулятор или подключите устройство"
    exit 1
fi

echo "Используем устройство: $DEVICE"
echo ""
echo "Запуск приложения..."
flutter run -d "$DEVICE"
