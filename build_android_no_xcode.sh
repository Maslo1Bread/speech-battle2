#!/bin/bash
echo "=== Сборка Android без проверки Xcode ==="
echo ""

# Экспортируем переменную, чтобы Flutter не проверял iOS
export FLUTTER_FORCE_NO_XCODE_CHECK=1
export FLUTTER_IOS_NO_XCODE_CHECK=1

# Очищаем кэш Flutter
echo "1. Очищаем кэш Flutter..."
flutter clean

# Получаем зависимости
echo "2. Получаем зависимости..."
flutter pub get

# Собираем APK
echo "3. Собираем APK..."
flutter build apk --no-tree-shake-icons

# Устанавливаем на устройство
echo "4. Устанавливаем на устройство..."
flutter install

echo ""
echo "=== Готово! ==="
echo "Если хотите запустить приложение:"
echo "flutter run -d android"
