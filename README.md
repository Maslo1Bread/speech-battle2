# Speech-Battle — Тренажёр переговоров

Мобильное приложение для тренировки навыков переговоров с ИИ-оппонентом или живыми игроками.

**Технологии:** Flutter (клиент) + FastAPI (бэкенд) + Groq API (ИИ)

---

## 📋 Содержание

- [Системные требования](#-системные-требования)
- [Установка на чистом ПК](#-установка-на-чистом-пк)
- [Запуск проекта](#-запуск-проекта)
- [Настройка русской клавиатуры](#-настройка-русской-клавиатуры)
- [Разработка](#-разработка)
- [Устранение неполадок](#-устранение-неполадок)

---

## 🖥️ Системные требования

### Обязательно:
- **macOS** 12.0+ (Monterey или новее)
- **Python** 3.11+
- **Flutter** 3.13+
- **Android Studio** (для эмуляторов)
- **Xcode** 15+ (для iOS, опционально)

### Минимальные характеристики:
- **RAM:** 8 ГБ (рекомендуется 16 ГБ)
- **Место на диске:** 20 ГБ
- **Процессор:** Intel Core i5 / Apple M1 и выше

---

## 🚀 Установка на чистом ПК

### Шаг 1: Установка Homebrew (менеджер пакетов)

Откройте Terminal и выполните:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

После установки добавьте brew в PATH (следуйте инструкциям в терминале):

```bash
# Для Apple Silicon (M1/M2/M3):
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# Для Intel Mac:
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/usr/local/bin/brew shellenv)"
```

Проверьте установку:

```bash
brew --version
```

---

### Шаг 2: Установка Python

```bash
# Установка Python через Homebrew
brew install python@3.11

# Проверка версии
python3 --version  # должно показать Python 3.11.x или выше

# Установка pip (если не установлен)
python3 -m pip install --upgrade pip
```

---

### Шаг 3: Установка Flutter

#### Вариант A: Через Homebrew (рекомендуется)

```bash
brew install flutter
```

#### Вариант B: Вручную (если нужна конкретная версия)

```bash
# Скачайте Flutter SDK
cd ~/Downloads
curl -LO https://storage.googleapis.com/flutter_infra_release/releases/stable/macos/flutter_macos_3.47.4-stable.zip

# Распакуйте
unzip flutter_macos_3.47.4-stable.zip

# Переместите в удобное место
sudo mv flutter /usr/local/

# Добавьте в PATH
echo 'export PATH="$PATH:/usr/local/flutter/bin"' >> ~/.zshrc
source ~/.zshrc
```

#### Настройка Flutter

```bash
# Проверьте установку
flutter doctor

# Примите лицензии Android
flutter doctor --android-licenses
```

---

### Шаг 4: Установка Android Studio

1. **Скачайте Android Studio:** https://developer.android.com/studio

2. **Установите:**
   - Откройте `.dmg` файл
   - Перетащите Android Studio в Applications
   - Запустите Android Studio

3. **Первоначальная настройка:**
   - Выберите "Standard" установку
   - Скачайте все предложенные компоненты
   - Дождитесь завершения установки

4. **Создайте эмулятор:**
   - Откройте Android Studio
   - Configure → AVD Manager → Create Device
   - Выберите **Pixel 6** или **Pixel 7 Pro**
   - Выберите системный образ **Android 14 (API 34)** или новее
   - Завершите создание

5. **Добавьте Android SDK в PATH:**

```bash
# Добавьте в ~/.zshrc
echo 'export ANDROID_HOME=$HOME/Library/Android/sdk' >> ~/.zshrc
echo 'export PATH=$PATH:$ANDROID_HOME/emulator' >> ~/.zshrc
echo 'export PATH=$PATH:$ANDROID_HOME/platform-tools' >> ~/.zshrc
source ~/.zshrc
```

Проверьте:

```bash
adb version
emulator -version
```

---

### Шаг 5: Установка Xcode (для iOS, опционально)

1. Скачайте Xcode из Mac App Store (бесплатно, ~12 ГБ)

2. После установки выполните:

```bash
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -runFirstLaunch
```

3. Примите лицензию:

```bash
sudo xcodebuild -license accept
```

---

### Шаг 6: Установка VS Code (рекомендуемый редактор)

```bash
brew install --cask visual-studio-code
```

Установите расширения:
- Flutter
- Dart
- Python

---

### Шаг 7: Клонирование проекта

```bash
# Перейдите в папку проектов
cd ~/StudioProjects  # или ~/Projects, ~/Development и т.д.

# Клонируйте репозиторий
git clone <URL_РЕПОЗИТОРИЯ> speech
cd speech
```

---

### Шаг 8: Настройка бэкенда

```bash
# Создайте виртуальное окружение
python3 -m venv .venv

# Активируйте его
source .venv/bin/activate

# Установите зависимости
pip install -r requirements.txt

# Скопируйте .env файл
cp .env.example .env

# Отредактируйте .env (добавьте GROQ_API_KEY если есть)
nano .env
```

---

### Шаг 9: Настройка Flutter проекта

```bash
# Получите зависимости Flutter
flutter pub get

# Сгенерируйте локализацию (если используется)
flutter gen-l10n

# Проверьте готовность
flutter doctor
```

---

## 🎮 Запуск проекта

### 1. Запуск бэкенда

**В первом терминале:**

```bash
cd ~/StudioProjects/speech

# Активируйте виртуальное окружение
source .venv/bin/activate

# Запустите бэкенд
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 9201
```

Проверьте работу бэкенда: http://127.0.0.1:9201/api/health

Должен вернуть: `{"status":"ok","backend":"running"}`

---

### 2. Запуск эмулятора

**Вариант A: Через Android Studio**

1. Откройте Android Studio
2. Configure → AVD Manager
3. Нажмите ▶️ Play на нужном эмуляторе

**Вариант B: Через терминал**

```bash
# Список доступных эмуляторов
emulator -list-avds

# Запуск эмулятора (в фоновом режиме)
emulator -avd Pixel_10_Pro &

# Или для SpeechPhone
emulator -avd SpeechPhone &
```

---

### 3. Настройка русской клавиатуры на эмуляторе

**Выполните один раз после первого запуска эмулятора:**

```bash
cd ~/StudioProjects/speech

# Дайте права на выполнение
chmod +x scripts/*.sh

# Запустите полную настройку
./scripts/full_russian_setup.sh

# Проверьте статус
./scripts/check_russian_keyboard.sh
```

**Ручная настройка (если скрипт не работает):**

```bash
# Откройте настройки клавиатуры на эмуляторе
~/Library/Android/sdk/platform-tools/adb shell "am start -a android.settings.INPUT_METHOD_SETTINGS"

# На эмуляторе:
# 1. Settings → System → Languages → Keyboard
# 2. Добавьте "Russian" в список языков
```

---

### 4. Запуск приложения Flutter

**Во втором терминале:**

```bash
cd ~/StudioProjects/speech

# Проверьте доступные устройства
flutter devices

# Запустите на эмуляторе
flutter run

# Или укажите конкретное устройство
flutter run -d emulator-5554
```

---

### 5. Быстрый запуск (все в одном)

Создайте алиасы для удобства:

```bash
# Добавьте в ~/.zshrc
echo 'alias speech-backend="cd ~/StudioProjects/speech && source .venv/bin/activate && uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 9201"' >> ~/.zshrc
echo 'alias speech-app="cd ~/StudioProjects/speech && flutter run"' >> ~/.zshrc
echo 'alias speech-emu="~/Library/Android/sdk/emulator/emulator -avd SpeechPhone &"' >> ~/.zshrc
source ~/.zshrc
```

Теперь можно запускать командами:

```bash
# Терминал 1: Бэкенд
speech-backend

# Терминал 2: Эмулятор + Приложение
speech-emu && sleep 10 && speech-app
```

---

## ⌨️ Настройка русской клавиатуры

### Автоматическая настройка

```bash
cd ~/StudioProjects/speech
./scripts/full_russian_setup.sh
```

### Как переключить клавиатуру на русский

**Способ 1: На клавиатуре эмулятора**
1. Нажмите на текстовое поле
2. Нажмите **глобус 🌐** или **пробел и удерживайте**
3. Выберите "Русский"

**Способ 2: Через настройки**
1. Settings → System → Languages → Keyboard
2. Выберите "Russian"

**Способ 3: Через ADB**
```bash
~/Library/Android/sdk/platform-tools/adb shell "am start -a android.settings.INPUT_METHOD_SETTINGS"
```
##Кириллица работает только на виртуальной клавиатуре на виртуальном устройстве!
### Скрипты для работы с клавиатурой

| Скрипт | Описание |
|--------|----------|
| `scripts/configure_emulators_russian.sh` | Настройка конфигурации эмуляторов |
| `scripts/setup_russian_keyboard.sh` | Настройка клавиатуры на запущенных эмуляторах |
| `scripts/check_russian_keyboard.sh` | Проверка статуса |
| `scripts/full_russian_setup.sh` | Полная настройка (рекомендуется) |

---

## 🛠️ Разработка

### Структура проекта

```
speech/
├── backend/              # FastAPI бэкенд
│   ├── app/
│   │   ├── main.py      # Точка входа
│   │   ├── routers/     # API роуты
│   │   └── models/      # Модели данных
│   └── scenarios/       # Сценарии переговоров
├── lib/                  # Flutter клиент
│   ├── main.dart        # Точка входа
│   ├── screens/         # Экраны приложения
│   ├── widgets/         # Переиспользуемые виджеты
│   ├── services/        # API сервисы
│   ├── state/           # Управление состоянием
│   └── theme/           # Темы и стили
├── scripts/              # Скрипты автоматизации
├── android/              # Android конфигурация
├── ios/                  # iOS конфигурация
├── .env                  # Переменные окружения
├── requirements.txt      # Python зависимости
└── pubspec.yaml         # Flutter зависимости
```

### Основные зависимости

**Backend (Python):**
- FastAPI
- SQLAlchemy
- PyJWT
- httpx
- python-multipart

**Frontend (Flutter):**
- flutter_localizations
- speech_to_text
- http
- web_socket_channel
- shared_preferences

### Переменные окружения (.env)

```bash
# Секрет для JWT (смените в продакшене!)
SECRET_KEY=your-secret-key-here

# API ключ Groq для ИИ-ответов (опционально)
# Получите здесь: https://console.groq.com
GROQ_API_KEY=gsk_xxxxx

# Данные админа по умолчанию
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@speech-battle.local
```

### Полезные команды Flutter

```bash
# Получить зависимости
flutter pub get

# Обновить зависимости
flutter pub upgrade

# Анализ кода
flutter analyze

# Форматирование кода
flutter format .

# Запуск тестов
flutter test

# Сборка APK
flutter build apk --release

# Сборка для iOS
flutter build ios --release

# Очистка кэша
flutter clean
```

### Hot Reload

При запущенном приложении:
- `r` - Hot reload (быстрое обновление UI)
- `R` - Hot restart (полный перезапуск)
- `q` - Выход

---

## 🔧 Устранение неполадок

### Проблема: Flutter не найден

**Решение:**

```bash
# Проверьте PATH
echo $PATH

# Добавьте Flutter в PATH (если установлен через Homebrew)
echo 'export PATH="$PATH:/opt/homebrew/bin/flutter"' >> ~/.zshrc
source ~/.zshrc

# Или если установлен вручную
echo 'export PATH="$PATH:/usr/local/flutter/bin"' >> ~/.zshrc
source ~/.zshrc
```

---

### Проблема: Android SDK не найден

**Решение:**

```bash
# Установите переменные окружения
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/platform-tools

# Добавьте в ~/.zshrc для постоянного использования
echo 'export ANDROID_HOME=$HOME/Library/Android/sdk' >> ~/.zshrc
echo 'export PATH=$PATH:$ANDROID_HOME/emulator' >> ~/.zshrc
echo 'export PATH=$PATH:$ANDROID_HOME/platform-tools' >> ~/.zshrc
source ~/.zshrc
```

---

### Проблема: Эмулятор не запускается

**Решение:**

```bash
# Проверьте список эмуляторов
emulator -list-avds

# Удалите старые эмуляторы и создайте новые
# Через Android Studio: Configure → AVD Manager → Delete

# Или создайте через командную строку
avdmanager create avd \
  -n SpeechPhone \
  -k "system-images;android-34;google_apis_playstore;arm64-v8a" \
  -d "pixel_6"
```

---

### Проблема: Бэкенд не запускается

**Решение:**

```bash
# Проверьте, что порт 9201 свободен
lsof -i :9201

# Если занят, убейте процесс
kill -9 <PID>

# Пересоздайте виртуальное окружение
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### Проблема: Приложение не подключается к бэкенду

**Решение:**

1. **Убедитесь, что бэкенд запущен:**
   ```bash
   curl http://127.0.0.1:9201/api/health
   ```

2. **Для Android эмулятора используйте:**
   ```bash
   # В приложении автоматически используется http://10.0.2.2:9201
   # Проверьте конфигурацию в lib/config.dart
   ```

3. **Для физического устройства:**
   ```bash
   # Узнайте IP компьютера
   ifconfig | grep "inet " | grep -v 127.0.0.1

   # Запустите с указанием IP
   flutter run --dart-define=API_BASE=http://192.168.1.XXX:9201
   ```

---

### Проблема: Русская клавиатура не работает

**Решение:**

```bash
# 1. Перезапустите эмулятор
# Закройте эмулятор и запустите снова

# 2. Выполните скрипт настройки
./scripts/full_russian_setup.sh

# 3. Откройте настройки клавиатуры вручную
~/Library/Android/sdk/platform-tools/adb shell "am start -a android.settings.INPUT_METHOD_SETTINGS"

# 4. Добавьте русский язык:
# Settings → System → Languages → Add language → Russian
```

---

### Проблема: Ошибки компиляции Flutter

**Решение:**

```bash
# Очистите проект
flutter clean

# Удалите кэш
rm -rf ~/.pub-cache
rm -rf .dart_tool

# Обновите зависимости
flutter pub upgrade

# Перезапустите IDE
```

---

### Проблема: Xcode ошибки (iOS)

**Решение:**

```bash
# Обновите CocoaPods
cd ios
pod deintegrate
pod install
cd ..

# Сбросьте симулятор
xcrun simctl erase all

# Откройте Xcode и соберите проект вручную
open ios/Runner.xcworkspace
```

---

## 📚 Дополнительные ресурсы

### Документация:
- [Flutter Documentation](https://docs.flutter.dev)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Android Emulator Guide](https://developer.android.com/studio/run/emulator)

### API эндпоинты:

После запуска бэкенда доступна документация:
- Swagger UI: http://127.0.0.1:9201/docs
- ReDoc: http://127.0.0.1:9201/redoc

### Поддержка:

Если возникли проблемы:
1. Проверьте раздел [Устранение неполадок](#-устранение-неполадок)
2. Выполните `flutter doctor` и исправьте найденные проблемы
3. Проверьте логи бэкенда и приложения

---

## 🎯 Быстрый старт (TL;DR)

```bash
# 1. Установите зависимости (один раз)
brew install python@3.11 flutter
brew install --cask android-studio visual-studio-code

# 2. Клонируйте проект
git clone <URL> speech && cd speech

# 3. Настройте бэкенд
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 4. Настройте Flutter
flutter pub get

# 5. Запустите эмулятор (в Android Studio или терминале)
emulator -avd SpeechPhone &

# 6. Настройте русскую клавиатуру
./scripts/full_russian_setup.sh

# 7. Запустите бэкенд (терминал 1)
source .venv/bin/activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 9201

# 8. Запустите приложение (терминал 2)
flutter run
```

---

## ✅ Чек-лист установки

- [ ] Homebrew установлен
- [ ] Python 3.11+ установлен
- [ ] Flutter установлен и в PATH
- [ ] Android Studio установлена
- [ ] Android SDK добавлен в PATH
- [ ] Эмулятор создан
- [ ] Проект клонирован
- [ ] Python зависимости установлены
- [ ] Flutter зависимости установлены
- [ ] Бэкенд запускается успешно
- [ ] Эмулятор запускается
- [ ] Русская клавиатура настроена
- [ ] Приложение запускается на эмуляторе
- [ ] Ввод русского текста работает

---

**Приятной работы с Speech-Battle! 🎤**


---

## 🪟 Установка на Windows

### Системные требования
- **Windows 10/11** (64-bit)
- **RAM:** 8 ГБ (рекомендуется 16 ГБ)
- **Место на диске:** 20 ГБ
- **BIOS:** Включенная виртуализация (Intel VT-x / AMD-V)

---

### Шаг 1: Установка Chocolatey (менеджер пакетов)

Откройте **PowerShell от имени администратора** и выполните:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

Проверьте установку:

```powershell
choco --version
```

---

### Шаг 2: Установка Git

```powershell
choco install git -y
```

После установки **перезапустите PowerShell**.

---

### Шаг 3: Установка Python

```powershell
choco install python311 -y
```

Проверьте:

```powershell
python --version
pip --version
```

---

### Шаг 4: Установка Flutter

#### Вариант A: Через Chocolatey (рекомендуется)

```powershell
choco install flutter -y
```

#### Вариант B: Вручную

1. Скачайте Flutter SDK: https://docs.flutter.dev/get-started/install/windows

2. Распакуйте в `C:\flutter`

3. Добавьте в PATH:
   - Откройте «Параметры системы» → «Дополнительно» → «Переменные среды»
   - В разделе «Системные переменные» найдите `Path`
   - Добавьте: `C:\flutter\bin`

4. Проверьте в PowerShell:
   ```powershell
   flutter --version
   ```

---

### Шаг 5: Установка Android Studio

1. **Скачайте Android Studio:** https://developer.android.com/studio

2. **Установите:**
   - Запустите `.exe` файл
   - Выберите "Standard" установку
   - Скачайте все компоненты

3. **Настройте Android SDK:**
   - Откройте Android Studio
   - Configure → SDK Manager
   - Установите Android SDK, Android SDK Platform-Tools, Android SDK Build-Tools

4. **Добавьте в PATH:**
   - Переменные среды → Системные переменные → `Path`
   - Добавьте:
     - `C:\Users\ВАШ_ПОЛЬЗОВАТЕЛЬ\AppData\Local\Android\Sdk\platform-tools`
     - `C:\Users\ВАШ_ПОЛЬЗОВАТЕЛЬ\AppData\Local\Android\Sdk\emulator`
     - `C:\Users\ВАШ_ПОЛЬЗОВАТЕЛЬ\AppData\Local\Android\Sdk\tools`

5. **Создайте переменную ANDROID_HOME:**
   - Имя: `ANDROID_HOME`
   - Значение: `C:\Users\ВАШ_ПОЛЬЗОВАТЕЛЬ\AppData\Local\Android\Sdk`

---

### Шаг 6: Включение виртуализации

1. **Проверьте поддержку виртуализации:**
   - Диспетчер задач → Производительность → ЦП
   - Должно быть написано "Виртуализация: Включена"

2. **Если выключена, включите в BIOS:**
   - Перезагрузите компьютер
   - Нажмите F2/Del/F12 для входа в BIOS
   - Найдите Intel VT-x или AMD-V
   - Включите (Enable)
   - Сохраните и выйдите

3. **Включите Hyper-V (Windows 11 Pro/Enterprise):**
   ```powershell
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   ```
   Перезагрузите компьютер.

---

### Шаг 7: Настройка Flutter

```powershell
flutter doctor
flutter doctor --android-licenses
```

Принимайте все лицензии (введите `y` и нажмите Enter).

---

### Шаг 8: Клонирование проекта

Откройте **PowerShell** или **Git Bash**:

```powershell
# Создайте папку проектов
mkdir C:\Projects
cd C:\Projects

# Клонируйте репозиторий
git clone <URL_РЕПОЗИТОРИЯ> speech
cd speech
```

---

### Шаг 9: Настройка бэкенда

```powershell
# Создайте виртуальное окружение
python -m venv .venv

# Активируйте его
.\.venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt

# Скопируйте .env файл
copy .env.example .env

# Отредактируйте при необходимости
notepad .env
```

---

### Шаг 10: Настройка Flutter проекта

```powershell
# Получите зависимости
flutter pub get

# Проверьте готовность
flutter doctor
```

---

### Шаг 11: Создание эмулятора

1. Откройте Android Studio
2. Configure → AVD Manager → Create Device
3. Выберите **Pixel 6** или **Pixel 7 Pro**
4. Выберите системный образ:
   - **Рекомендуется:** Android 14 (API 34) с Google Play
   - Для ARM: выберите образ с пометкой "Play Store"
   - Для x86: выберите образ без Play Store (быстрее)
5. Завершите создание

**Запуск эмулятора:**
- Через Android Studio: нажмите ▶️ Play
- Через PowerShell:
  ```powershell
  # Список эмуляторов
  emulator -list-avds
  
  # Запуск
  emulator -avd Pixel_6_API_34
  ```

---

### Шаг 12: Настройка русской клавиатуры на Windows

**Автоматическая настройка (через PowerShell):**

```powershell
cd C:\Projects\speech

# Создайте папку scripts если нет
mkdir scripts -Force

# Дайте права на выполнение (если скрипты есть)
Get-ChildItem scripts\*.sh | ForEach-Object { chmod +x $_.FullName }

# Для Android эмуляторов настройка аналогична macOS
# Используйте adb из Android SDK
$env:ANDROID_HOME\platform-tools\adb shell "settings put system system_locales ru-RU"
$env:ANDROID_HOME\platform-tools\adb shell "settings put secure selected_input_method_subtypes -921088104"
```

**Ручная настройка:**

1. Откройте настройки клавиатуры:
   ```powershell
   $env:ANDROID_HOME\platform-tools\adb shell "am start -a android.settings.INPUT_METHOD_SETTINGS"
   ```

2. На эмуляторе:
   - Settings → System → Languages → Keyboard
   - Добавьте "Russian"

---

### Шаг 13: Запуск проекта на Windows

**Терминал 1 (Бэкенд):**

```powershell
cd C:\Projects\speech
.\.venv\Scripts\activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 9201
```

**Терминал 2 (Приложение):**

```powershell
cd C:\Projects\speech

# Проверьте устройства
flutter devices

# Запустите
flutter run

# Или укажите конкретное устройство
flutter run -d emulator-5554
```

---

### Быстрые команды для Windows

Создайте файл `C:\Projects\speech\run.ps1`:

```powershell
# run_backend.ps1
cd C:\Projects\speech
.\.venv\Scripts\activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 9201
```

```powershell
# run_app.ps1
cd C:\Projects\speech
flutter run
```

```powershell
# setup_keyboard.ps1
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
& $adb shell "settings put system system_locales ru-RU"
& $adb shell "settings put secure selected_input_method_subtypes -921088104"
Write-Host "✅ Русская клавиатура настроена"
```

Запускайте:

```powershell
powershell -ExecutionPolicy Bypass -File run_backend.ps1
powershell -ExecutionPolicy Bypass -File run_app.ps1
powershell -ExecutionPolicy Bypass -File setup_keyboard.ps1
```

---

### Устранение неполадок на Windows

#### Проблема: Flutter не найден

**Решение:** Добавьте в PATH вручную:
- Параметры системы → Переменные среды
- Добавьте в `Path`: `C:\flutter\bin`
- Перезапустите PowerShell

#### Проблема: Android SDK не найден

**Решение:**
```powershell
# Установите переменную окружения
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
$env:Path += ";$env:ANDROID_HOME\platform-tools"
$env:Path += ";$env:ANDROID_HOME\emulator"

# Добавьте в профиль PowerShell для постоянного использования
Add-Content $PROFILE "`$env:ANDROID_HOME = `"`$env:LOCALAPPDATA\Android\Sdk`""
Add-Content $PROFILE "`$env:Path += `";`$env:ANDROID_HOME\platform-tools`""
```

#### Проблема: Эмулятор не запускается (HAXM error)

**Решение:**
1. Включите виртуализацию в BIOS
2. Установите HAXM:
   - Скачайте: https://github.com/intel/haxm/releases
   - Или через Android Studio: SDK Manager → SDK Tools → Intel x86 Emulator Accelerator

#### Проблема: Ошибка "Execution Policy"

**Решение:**
```powershell
# Разрешите выполнение скриптов
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Проблема: Антивирус блокирует Flutter

**Решение:**
- Добавьте исключение для папок:
  - `C:\flutter`
  - `C:\Users\ВАШ_ПОЛЬЗОВАТЕЛЬ\.flutter`
  - `C:\Projects\speech`

---

## 🐧 Установка на Linux (Ubuntu/Debian)

### Системные требования
- **Ubuntu 22.04+** / Debian 12+ / Fedora 38+ / Arch Linux
- **RAM:** 8 ГБ (рекомендуется 16 ГБ)
- **Место на диске:** 20 ГБ

---

### Шаг 1: Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

---

### Шаг 2: Установка Git

```bash
sudo apt install git -y
git --version
```

---

### Шаг 3: Установка Python

```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv -y

# Fedora
sudo dnf install python3 python3-pip -y

# Arch Linux
sudo pacman -S python python-pip

# Проверка
python3 --version
pip3 --version
```

---

### Шаг 4: Установка Flutter

#### Вариант A: Через Snap (Ubuntu, рекомендуется)

```bash
sudo snap install flutter --classic
```

#### Вариант B: Вручную (все дистрибутивы)

```bash
# Установите зависимости
sudo apt install curl git unzip xz-utils zip libglu1-mesa -y

# Fedora
sudo dnf install curl git unzip xz zlib -y

# Arch Linux
sudo pacman -S curl git unzip xz zlib

# Скачайте Flutter
cd ~/Downloads
curl -LO https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.47.4-stable.tar.xz

# Распакуйте
tar xf flutter_linux_3.47.4-stable.tar.xz

# Переместите
sudo mv flutter /opt/

# Добавьте в PATH
echo 'export PATH="$PATH:/opt/flutter/bin"' >> ~/.bashrc
source ~/.bashrc

# Проверьте
flutter --version
```

---

### Шаг 5: Установка Android Studio

#### Вариант A: Через Snap (Ubuntu)

```bash
sudo snap install android-studio --classic
```

#### Вариант B: Вручную

```bash
# Установите зависимости
sudo apt install libc6:amd64 libstdc++6:amd64 lib32z1 libbz2-1.0:amd64 -y

# Fedora
sudo dnf install zlib.i686 ncurses-libs.i686 bzip2-libs.i686

# Скачайте Android Studio
cd ~/Downloads
wget https://redirector.gvt1.com/edgedl/android/studio/ide-zips/2024.1.1.11/android-studio-2024.1.1.11-linux.tar.gz

# Распакуйте
sudo tar xf android-studio-*-linux.tar.gz -C /opt/

# Создайте ярлык
cat > ~/.local/share/applications/android-studio.desktop <<EOL
[Desktop Entry]
Version=1.0
Type=Application
Name=Android Studio
Comment=Android IDE
Exec=/opt/android-studio/bin/studio.sh %f
Icon=/opt/android-studio/bin/studio.png
Terminal=false
Categories=Development;IDE;
EOL

# Запустите
/opt/android-studio/bin/studio.sh
```

#### Первоначальная настройка Android Studio:

1. Запустите Android Studio
2. Выберите "Standard" установку
3. Скачайте компоненты
4. Примите лицензии

---

### Шаг 6: Настройка Android SDK

```bash
# Добавьте переменные окружения
echo 'export ANDROID_HOME=$HOME/Android/Sdk' >> ~/.bashrc
echo 'export PATH=$PATH:$ANDROID_HOME/emulator' >> ~/.bashrc
echo 'export PATH=$PATH:$ANDROID_HOME/platform-tools' >> ~/.bashrc
source ~/.bashrc

# Примите лицензии
flutter doctor --android-licenses
```

---

### Шаг 7: Установка KVM (для ускорения эмулятора)

**Проверьте поддержку виртуализации:**

```bash
# Intel
egrep -c '(vmx|svm)' /proc/cpuinfo
# Должно вернуть число > 0

# Установите KVM
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils -y

# Fedora
sudo dnf install @virtualization -y

# Arch Linux
sudo pacman -S qemu-headless libvirt virt-manager

# Добавьте пользователя в группу
sudo usermod -aG kvm $USER
sudo usermod -aG libvirt $USER

# Выйдите и войдите снова или:
newgrp kvm
```

**Проверьте KVM:**

```bash
kvm-ok
# Должно показать: "KVM acceleration can be used"
```

---

### Шаг 8: Настройка Flutter

```bash
flutter doctor -v
```

Исправьте все проблемы, которые покажет команда.

---

### Шаг 9: Клонирование проекта

```bash
# Создайте папку проектов
mkdir -p ~/Projects
cd ~/Projects

# Клонируйте
git clone <URL_РЕПОЗИТОРИЯ> speech
cd speech
```

---

### Шаг 10: Настройка бэкенда

```bash
# Создайте venv
python3 -m venv .venv

# Активируйте
source .venv/bin/activate

# Установите зависимости
pip install -r requirements.txt

# Создайте .env
cp .env.example .env

# Отредактируйте
nano .env
```

---

### Шаг 11: Настройка Flutter проекта

```bash
# Получите зависимости
flutter pub get

# Проверьте
flutter doctor
```

---

### Шаг 12: Создание эмулятора

**Через Android Studio:**
1. Откройте Android Studio
2. Configure → AVD Manager → Create Device
3. Выберите устройство (Pixel 6/7 Pro)
4. Выберите системный образ:
   - Для KVM: x86_64 образ (быстрее)
   - Без KVM: ARM образ (медленнее)
5. Завершите создание

**Через командную строку:**

```bash
# Установите системный образ
sdkmanager "system-images;android-34;google_apis_playstore;x86_64"

# Создайте эмулятор
avdmanager create avd \
  -n SpeechPhone \
  -k "system-images;android-34;google_apis_playstore;x86_64" \
  -d "pixel_6"

# Запустите
emulator -avd SpeechPhone &
```

---

### Шаг 13: Настройка русской клавиатуры на Linux

```bash
cd ~/Projects/speech

# Сделайте скрипты исполняемыми
chmod +x scripts/*.sh

# Запустите настройку
./scripts/full_russian_setup.sh

# Или вручную через adb
~/Android/Sdk/platform-tools/adb shell "settings put system system_locales ru-RU"
~/Android/Sdk/platform-tools/adb shell "settings put secure selected_input_method_subtypes -921088104"
```

---

### Шаг 14: Запуск проекта на Linux

**Терминал 1 (Бэкенд):**

```bash
cd ~/Projects/speech
source .venv/bin/activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 9201
```

**Терминал 2 (Приложение):**

```bash
cd ~/Projects/speech

# Запустите эмулятор (если не запущен)
~/Android/Sdk/emulator/emulator -avd SpeechPhone &

# Запустите приложение
flutter run
```

---

### Быстрые команды для Linux

Создайте алиасы в `~/.bashrc`:

```bash
# Speech-Battle алиасы
alias sb-backend="cd ~/Projects/speech && source .venv/bin/activate && uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 9201"
alias sb-run="cd ~/Projects/speech && flutter run"
alias sb-emu="~/Android/Sdk/emulator/emulator -avd SpeechPhone &"
alias sb-check="cd ~/Projects/speech && ./scripts/check_russian_keyboard.sh"
alias sb-devices="flutter devices"
alias sb-doctor="flutter doctor -v"
```

Примените:

```bash
source ~/.bashrc
```

Теперь запускайте:

```bash
sb-backend  # Терминал 1
sb-emu && sleep 10 && sb-run  # Терминал 2
```

---

### Скрипт для запуска на Linux

Создайте файл `~/Projects/speech/start.sh`:

```bash
#!/bin/bash
# Скрипт для запуска Speech-Battle на Linux

PROJECT_DIR="$HOME/Projects/speech"
ADB="$HOME/Android/Sdk/platform-tools/adb"
EMU="$HOME/Android/Sdk/emulator/emulator"

echo "🚀 Запуск Speech-Battle..."

# Проверяем, запущен ли бэкенд
if ! lsof -i :9201 > /dev/null 2>&1; then
    echo "⏳ Запуск бэкенда..."
    gnome-terminal -- bash -c "cd $PROJECT_DIR && source .venv/bin/activate && uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 9201; exec bash"
    sleep 3
else
    echo "✅ Бэкенд уже запущен"
fi

# Проверяем, запущен ли эмулятор
if ! $ADB devices | grep -q "emulator"; then
    echo "⏳ Запуск эмулятора..."
    $EMU -avd SpeechPhone &
    sleep 15
else
    echo "✅ Эмулятор уже запущен"
fi

# Настраиваем русскую клавиатуру
echo "⏳ Настройка русской клавиатуры..."
$ADB shell "settings put system system_locales ru-RU" 2>/dev/null
$ADB shell "settings put secure selected_input_method_subtypes -921088104" 2>/dev/null

# Запускаем приложение
echo "⏳ Запуск Flutter приложения..."
cd $PROJECT_DIR
flutter run

echo "👋 Готово!"
```

Сделайте исполняемым:

```bash
chmod +x ~/Projects/speech/start.sh
```

Запускайте одной командой:

```bash
~/Projects/speech/start.sh
```

---

### Устранение неполадок на Linux

#### Проблема: Flutter не найден

**Решение:**
```bash
# Проверьте PATH
echo $PATH

# Добавьте Flutter вручную
echo 'export PATH="$PATH:/opt/flutter/bin"' >> ~/.bashrc
source ~/.bashrc
```

#### Проблема: Android SDK не найден

**Решение:**
```bash
# Установите переменные
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/platform-tools

# Добавьте в bashrc
echo 'export ANDROID_HOME=$HOME/Android/Sdk' >> ~/.bashrc
echo 'export PATH=$PATH:$ANDROID_HOME/emulator' >> ~/.bashrc
echo 'export PATH=$PATH:$ANDROID_HOME/platform-tools' >> ~/.bashrc
source ~/.bashrc
```

#### Проблема: KVM не работает

**Решение:**
```bash
# Проверьте поддержку
kvm-ok

# Если ошибка, добавьте пользователя в группы
sudo usermod -aG kvm $USER
sudo usermod -aG libvirt $USER

# Выйдите и войдите снова
logout
```

#### Проблема: Ошибка "/dev/kvm not found"

**Решение:**
```bash
# Проверьте наличие KVM
ls -la /dev/kvm

# Если нет, перезагрузите систему
sudo reboot

# После перезагрузки проверьте снова
kvm-ok
```

#### Проблема: Медленный эмулятор

**Решение:**
1. Используйте x86_64 образы (быстрее с KVM)
2. Выделите больше RAM эмулятору (в AVD Manager)
3. Включите GPU ускорение:
   ```bash
   # Проверьте поддержку GPU
   glxinfo | grep "OpenGL renderer"
   ```

#### Проблема: Ошибка "Unable to locate package"

**Решение:**
```bash
# Обновите списки пакетов
sudo apt update

# Для Fedora
sudo dnf clean all
sudo dnf makecache

# Для Arch Linux
sudo pacman -Sy
```

#### Проблема: Русская клавиатура не работает

**Решение:**
```bash
# Откройте настройки клавиатуры на эмуляторе
~/Android/Sdk/platform-tools/adb shell "am start -a android.settings.INPUT_METHOD_SETTINGS"

# Или выполните скрипт
cd ~/Projects/speech
./scripts/full_russian_setup.sh
```

---

## 📊 Сравнение платформ

| Платформа | Сложность установки | Скорость эмулятора | Рекомендации |
|-----------|-------------------|-------------------|--------------|
| **macOS** | ⭐⭐⭐ (средняя) | ⭐⭐⭐⭐⭐ (быстро, M1/M2/M3) | Лучший выбор для iOS разработки |
| **Windows** | ⭐⭐⭐⭐ (сложная) | ⭐⭐⭐ (средне) | Требует настройки виртуализации |
| **Linux** | ⭐⭐ (простая) | ⭐⭐⭐⭐ (быстро с KVM) | Лучший выбор для серверов и разработки |

### Рекомендации по выбору платформы:

**macOS:**
- ✅ Лучшая поддержка iOS разработки
- ✅ Быстрые эмуляторы на Apple Silicon
- ✅ Стабильная работа Flutter
- ❌ Дорогое оборудование

**Windows:**
- ✅ Широкая доступность
- ✅ Поддержка всех Android устройств
- ❌ Требует настройку виртуализации
- ❌ Нет iOS разработки

**Linux:**
- ✅ Бесплатная ОС
- ✅ Быстрые эмуляторы с KVM
- ✅ Отлично для серверов
- ❌ Нет iOS разработки
- ❌ Требует знания терминала

---

## 🎯 Быстрый старт на разных платформах

### macOS
```bash
brew install python@3.11 flutter
brew install --cask android-studio
git clone <URL> speech && cd speech
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
flutter pub get
./scripts/full_russian_setup.sh
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 9201 &
flutter run
```

### Windows (PowerShell)
```powershell
choco install python311 flutter android-studio git -y
git clone <URL> speech; cd speech
python -m venv .venv; .\.venv\Scripts\activate
pip install -r requirements.txt
flutter pub get
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 9201
flutter run
```

### Linux
```bash
sudo apt install python3 python3-pip git -y
sudo snap install flutter --classic
sudo snap install android-studio --classic
git clone <URL> speech && cd speech
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
flutter pub get
./scripts/full_russian_setup.sh
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 9201 &
flutter run
```

---
