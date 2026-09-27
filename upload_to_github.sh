#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Скрипт для загрузки Speech-Battle на GitHub
# ─────────────────────────────────────────────────────────────────

echo "🚀 Загрузка Speech-Battle на GitHub"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Проверяем, что мы в правильной папке
if [ ! -d ".git" ]; then
    echo "❌ Ошибка:这不是 Git репозиторий"
    echo "💡 Выполните: cd ~/Desktop/Speech-Battle2"
    exit 1
fi

# Проверяем статус Git
echo "📋 Проверка статуса Git..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Есть несохранённые изменения:"
    git status --short
    echo ""
    read -p "Зафиксировать изменения? (y/n): " commit_choice
    if [ "$commit_choice" = "y" ]; then
        git add .
        git commit -m "Update project files"
        echo "✅ Изменения зафиксированы"
    fi
else
    echo "✅ Все изменения сохранены"
fi

echo ""
echo "📝 Сейчас вам нужно:"
echo "   1. Открыть браузер: https://github.com/new"
echo "   2. Создать репозиторий с именем 'speech-battle'"
echo "   3. Скопировать URL репозитория"
echo ""
read -p "Нажмите Enter, когда создадите репозиторий..."

echo ""
echo "📋 Введите URL вашего репозитория GitHub:"
echo "   (например: https://github.com/YOUR_USERNAME/speech-battle.git)"
read -p "URL: " repo_url

# Проверяем, что URL не пустой
if [ -z "$repo_url" ]; then
    echo "❌ URL не может быть пустым"
    exit 1
fi

# Проверяем формат URL
if [[ ! "$repo_url" =~ ^https://github\.com/ ]]; then
    echo "⚠️  URL должен начинаться с https://github.com/"
    echo "   Пример: https://github.com/YOUR_USERNAME/speech-battle.git"
    exit 1
fi

echo ""
echo "🔗 Добавляем remote..."
git remote remove origin 2>/dev/null
git remote add origin "$repo_url"

echo "✅ Remote добавлен: $repo_url"
echo ""

# Проверяем, нужна ли аутентификация
echo "🔐 Для загрузки на GitHub вам понадобится:"
echo "   • Логин GitHub"
echo "   • Пароль ИЛИ Personal Access Token"
echo ""
echo "💡 Если у вас включена 2FA, используйте Personal Access Token:"
echo "   https://github.com/settings/tokens"
echo ""
read -p "Готовы продолжить? (y/n): " ready

if [ "$ready" != "y" ]; then
    echo "👋 Загрузка отменена"
    exit 0
fi

echo ""
echo "⏳ Загрузка на GitHub..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Пытаемся загрузить
if git push -u origin main; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎉 Успешно загружено на GitHub!"
    echo ""
    echo "📦 Ваш репозиторий:"
    # Извлекаем URL без .git
    repo_url_clean="${repo_url%.git}"
    echo "   $repo_url_clean"
    echo ""
    echo "✅ Что дальше:"
    echo "   1. Откройте репозиторий в браузере"
    echo "   2. Проверьте, что README.md отображается"
    echo "   3. Добавьте темы (topics): flutter, fastapi, ai"
    echo ""
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ Ошибка загрузки"
    echo ""
    echo "🔧 Возможные причины:"
    echo "   1. Неверный логин или пароль"
    echo "   2. Репозиторий уже существует"
    echo "   3. Нет прав на запись"
    echo ""
    echo "💡 Попробуйте:"
    echo "   1. Проверьте URL репозитория"
    echo "   2. Используйте Personal Access Token вместо пароля"
    echo "   3. Убедитесь, что репозиторий создан на GitHub"
    echo ""
    echo "🔐 Создать токен: https://github.com/settings/tokens/new"
    echo "   Выберите права: repo (full control)"
    echo ""
fi
