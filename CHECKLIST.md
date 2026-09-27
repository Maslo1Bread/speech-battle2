# ✅ Чек-лист установки Speech-Battle

Распечатайте и отмечайте выполненные шаги.

---

## 📋 Этап 1: Подготовка системы

- [ ] **Homebrew установлен**
  ```bash
  brew --version
  ```

- [ ] **Python 3.11+ установлен**
  ```bash
  python3 --version
  ```

- [ ] **Flutter установлен**
  ```bash
  flutter --version
  ```

- [ ] **Android Studio установлена**
  - Откройте Android Studio
  - Пройдите первоначальную настройку

- [ ] **Android SDK в PATH**
  ```bash
  echo $ANDROID_HOME
  # Должно показать: /Users/YOUR_NAME/Library/Android/sdk
  ```

---

## 📋 Этап 2: Установка проекта

- [ ] **Проект клонирован**
  ```bash
  cd ~/StudioProjects
  git clone <URL> speech
  cd speech
  ```

- [ ] **Python venv создан**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

- [ ] **Python зависимости установлены**
  ```bash
  pip install -r requirements.txt
  ```

- [ ] **.env файл создан**
  ```bash
  cp .env.example .env
  # Отредактируйте при необходимости
  ```

- [ ] **Flutter зависимости установлены**
  ```bash
  flutter pub get
  ```

---

## 📋 Этап 3: Настройка эмулятора

- [ ] **Эмулятор создан**
  - В Android Studio: Configure → AVD Manager
  - Создайте Pixel 6 или Pixel 7 Pro
  - Системный образ: Android 14+ (API 34+)

- [ ] **Эмулятор запускается**
  ```bash
  ~/Library/Android/sdk/emulator/emulator -list-avds
  ~/Library/Android/sdk/emulator/emulator -avd YOUR_EMULATOR_NAME &
  ```

- [ ] **ADB работает**
  ```bash
  ~/Library/Android/sdk/platform-tools/adb devices
  # Должен показать список эмуляторов
  ```

---

## 📋 Этап 4: Настройка русской клавиатуры

- [ ] **Скрипты имеют права на выполнение**
  ```bash
  chmod +x scripts/*.sh
  ```

- [ ] **Русская клавиатура настроена**
  ```bash
  ./scripts/full_russian_setup.sh
  ```

- [ ] **Статус проверен**
  ```bash
  ./scripts/check_russian_keyboard.sh
  # Все галочки должны быть ✅
  ```

---

## 📋 Этап 5: Запуск проекта

- [ ] **Бэкенд запускается**
  ```bash
  source .venv/bin/activate
  uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 9201
  ```
  Проверка: http://127.0.0.1:9201/api/health

- [ ] **Приложение запускается**
  ```bash
  flutter run
  ```

- [ ] **Приложение видит бэкенд**
  - Откройте приложение на эмуляторе
  - Попробуйте войти или зарегистрироваться

---

## 📋 Этап 6: Финальная проверка

- [ ] **Ввод русского текста работает**
  - Откройте чат в приложении
  - Введите сообщение на русском
  - Отправьте сообщение

- [ ] **Голосовой ввод работает** (опционально)
  - Нажмите на иконку микрофона
  - Дайте разрешение на запись
  - Произнесите текст на русском

- [ ] **ИИ-оппонент отвечает**
  - Выберите сценарий
  - Начните переговоры с ИИ
  - Получите ответ

---

## 🐛 Если что-то не работает

### Flutter проблемы
```bash
flutter doctor -v
flutter clean
flutter pub get
```

### Бэкенд проблемы
```bash
lsof -i :9201  # проверьте, свободен ли порт
pkill -f uvicorn  # убейте старые процессы
```

### Эмулятор проблемы
```bash
# Перезапустите ADB
~/Library/Android/sdk/platform-tools/adb kill-server
~/Library/Android/sdk/platform-tools/adb start-server

# Перезапустите эмулятор
```

### Клавиатура проблемы
```bash
./scripts/full_russian_setup.sh
~/Library/Android/sdk/platform-tools/adb shell "am start -a android.settings.INPUT_METHOD_SETTINGS"
```

---

## 📚 Полезные ссылки

- **Flutter Doctor:** `flutter doctor -v`
- **API документация:** http://127.0.0.1:9201/docs
- **Полный README:** [README.md](README.md)
- **Быстрый старт:** [QUICKSTART.md](QUICKSTART.md)

---

**Дата установки:** _______________

**Время установки:** _______________ минут

**Проблемы и решения:**
_____________________________________
_____________________________________
_____________________________________
