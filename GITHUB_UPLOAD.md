# 📤 Загрузка проекта на GitHub

Проект готов к загрузке! Папка `Speech-Battle` находится на вашем рабочем столе.

---

## 📋 Что включено в проект

✅ **152 файла** готовы к загрузке
✅ **Размер:** ~10 МБ
✅ **Git репозиторий инициализирован**
✅ **Initial commit создан**

### Структура проекта:
- `lib/` - Flutter мобильное приложение
- `backend/` - FastAPI бэкенд
- `android/` - Android конфигурация
- `scripts/` - Скрипты для настройки русской клавиатуры
- `README.md` - Подробная инструкция для macOS, Windows, Linux
- `QUICKSTART.md` - Быстрый старт
- `CHECKLIST.md` - Чек-лист установки

### Исключено (не загружается):
- `.env` - секретные ключи (используйте `.env.example`)
- `build/` - собранные файлы
- `.dart_tool/` - кэш Flutter
- `.venv/` - виртуальное окружение Python
- `.idea/` - настройки IDE
- `*.db` - базы данных
- `*.log` - логи

---

## 🚀 Загрузка на GitHub

### Шаг 1: Создайте репозиторий на GitHub

1. Откройте https://github.com/new
2. Заполните форму:
   - **Repository name:** `speech-battle` (или другое название)
   - **Description:** `Speech-Battle — тренажёр переговоров. Flutter mobile app + FastAPI backend`
   - **Public** или **Private** (по вашему выбору)
   - ❌ **НЕ** ставьте галочку "Add a README file"
   - ❌ **НЕ** ставьте галочку "Add .gitignore"
   - ❌ **НЕ** выбирайте лицензию
3. Нажмите **Create repository**

### Шаг 2: Загрузите проект

**Вариант A: Через GitHub CLI (рекомендуется)**

```bash
cd ~/Desktop/Speech-Battle

# Если установлен GitHub CLI (gh)
gh repo create speech-battle --public --source=. --push

# Или для приватного репозитория
gh repo create speech-battle --private --source=. --push
```

**Вариант B: Через HTTPS (стандартный способ)**

GitHub покажет команды после создания репозитория. Они будут выглядеть так:

```bash
cd ~/Desktop/Speech-Battle

# Добавьте remote (замените YOUR_USERNAME на ваш логин GitHub)
git remote add origin https://github.com/YOUR_USERNAME/speech-battle.git

# Переименуйте ветку в main (если нужно)
git branch -M main

# Загрузите код
git push -u origin main
```

**Вариант C: Через SSH (если настроен SSH ключ)**

```bash
cd ~/Desktop/Speech-Battle

# Добавьте remote
git remote add origin git@github.com:YOUR_USERNAME/speech-battle.git

# Загрузите код
git branch -M main
git push -u origin main
```

### Шаг 3: Проверьте загрузку

1. Откройте ваш репозиторий на GitHub: https://github.com/YOUR_USERNAME/speech-battle
2. Убедитесь, что все файлы загружены
3. Проверьте README.md - он должен отображаться на главной странице

---

## 🔐 Важные замечания

### ⚠️ Секретные ключи

**Файл `.env` НЕ загружен на GitHub** (исключён в .gitignore)

Перед запуском проекта:
1. Скопируйте `.env.example` в `.env`
2. Заполните секретные ключи:
   ```bash
   cp .env.example .env
   nano .env
   ```

### 🔑 Необходимые ключи:

- `SECRET_KEY` - секрет для JWT (смените на свой!)
- `GROQ_API_KEY` - ключ для ИИ (опционально, получите на https://console.groq.com)
- `ADMIN_USERNAME`, `ADMIN_PASSWORD` - данные админа по умолчанию

---

## 📝 После загрузки

### 1. Добавьте описание репозитория

На странице репозитория нажмите ⚙️ Settings:
- Description: `Speech-Battle — тренажёр переговоров с ИИ`
- Website: можно оставить пустым
- Topics: `flutter`, `fastapi`, `negotiation-training`, `ai`, `mobile-app`

### 2. Настройте GitHub Pages (опционально)

Если хотите показать документацию:
1. Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main` → `/ (root)` → Save

### 3. Пригласите команду (если нужно)

Settings → Collaborators → Add people

---

## 🎯 Быстрая проверка

После загрузки проверьте на GitHub:

✅ README.md отображается на главной странице
✅ Все папки на месте: `lib/`, `backend/`, `android/`
✅ Файл `.env` ОТСУТСТВУЕТ (это правильно!)
✅ Код можно клонировать: `git clone https://github.com/YOUR_USERNAME/speech-battle.git`

---

## 📊 Статистика проекта

- **Языки программирования:**
  - Dart (Flutter): ~70%
  - Python (FastAPI): ~25%
  - Kotlin/Shell/Other: ~5%

- **Основные функции:**
  - ✅ Мобильное приложение Flutter
  - ✅ FastAPI бэкенд
  - ✅ Интеграция с Groq AI
  - ✅ Голосовой ввод
  - ✅ Поддержка русского языка
  - ✅ Документация для 3 платформ

---

## 🆘 Если возникли проблемы

### Ошибка: "fatal: 'origin' already exists"

```bash
cd ~/Desktop/Speech-Battle
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/speech-battle.git
git push -u origin main
```

### Ошибка: "fatal: Authentication failed"

1. Проверьте логин и пароль GitHub
2. Или используйте Personal Access Token:
   - GitHub → Settings → Developer settings → Personal access tokens
   - Создайте токен с правами `repo`
   - Используйте токен как пароль

### Ошибка: "Updates were rejected"

```bash
cd ~/Desktop/Speech-Battle
git pull origin main --rebase
git push origin main
```

---

## ✅ Готово!

После успешной загрузки:
1. ✅ Проект доступен по адресу: https://github.com/YOUR_USERNAME/speech-battle
2. ✅ README.md автоматически отображается на главной странице
3. ✅ Другие разработчики могут клонировать проект
4. ✅ Можно создавать ветки, Pull Requests и т.д.

**Удачи с проектом! 🎉**
