# ⚡ Быстрый старт Speech-Battle

## Минимальная установка (5-10 минут)

### 1. Установите Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Установите всё сразу
```bash
brew install python@3.11 flutter
brew install --cask android-studio visual-studio-code
```

### 3. Настройте Flutter
```bash
flutter doctor
flutter doctor --android-licenses
```

### 4. Скачайте проект
```bash
cd ~/StudioProjects  # или ваша папка проектов
git clone <URL_РЕПОЗИТОРИЯ> speech
cd speech
```

### 5. Установите зависимости
```bash
# Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Flutter
flutter pub get
```

### 6. Запустите!

**Терминал 1 (Бэкенд):**
```bash
cd ~/StudioProjects/speech
source .venv/bin/activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 9201
```

**Терминал 2 (Эмулятор + Приложение):**
```bash
# Запустите эмулятор в Android Studio или:
~/Library/Android/sdk/emulator/emulator -avd SpeechPhone &

# Настройте русскую клавиатуру (один раз)
cd ~/StudioProjects/speech
chmod +x scripts/*.sh
./scripts/full_russian_setup.sh

# Запустите приложение
flutter run
```

---

## Алиасы для быстрой работы

Добавьте в `~/.zshrc`:

```bash
alias sb-backend="cd ~/StudioProjects/speech && source .venv/bin/activate && uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 9201"
alias sb-run="cd ~/StudioProjects/speech && flutter run"
alias sb-emu="~/Library/Android/sdk/emulator/emulator -avd SpeechPhone &"
alias sb-check="cd ~/StudioProjects/speech && ./scripts/check_russian_keyboard.sh"
```

Примените:
```bash
source ~/.zshrc
```

Теперь запускайте просто:
```bash
sb-backend  # в первом терминале
sb-emu      # запустить эмулятор
sb-run      # запустить приложение
```

---

## Проверка работы

1. **Бэкенд:** http://127.0.0.1:9201/api/health → должен вернуть `{"status":"ok"}`
2. **Русская клавиатура:** `./scripts/check_russian_keyboard.sh` → все галочки ✅
3. **Приложение:** откройте на эмуляторе, введите русский текст

---

## Если что-то не работает

```bash
# Проверьте Flutter
flutter doctor -v

# Перезапустите всё
pkill -f uvicorn
pkill -f flutter
flutter clean
flutter pub get

# Настройте клавиатуру заново
./scripts/full_russian_setup.sh
```

---

## Полная документация

См. [README.md](README.md) для подробных инструкций.
