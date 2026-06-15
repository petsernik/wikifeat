#!/bin/bash

# Переходим в каталог, где находится сам скрипт
cd "$(dirname "$0")" || exit 1

# Создаем папку для временных файлов, если её нет
mkdir -p tmp

# Запоминаем текущую ветку
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

# Проверяем, есть ли изменения для stash
STASH_CREATED=0

if ! git diff --quiet || ! git diff --cached --quiet; then
    STASH_CREATED=1
    git stash push -m "auto-stash-before-script"
fi

# Переходим на master
git checkout master > tmp/log_checkout.txt 2>&1

# Обновляем проект
{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting update..."
    git pull
} > tmp/log_git.txt 2>&1

# Активируем виртуальное окружение (если есть), устанавливаем зависимости и запускаем Python
{
    if [ -f ".venv/bin/activate" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Virtual environment found. Activating..."
        # shellcheck disable=SC1091
        source .venv/bin/activate
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] No virtual environment found. Running without it."
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Check and install requirements..."
    pip install -r requirements.txt

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running script.py..."
    python script.py

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Script finished."
} > tmp/log.txt 2>&1

# Возвращаем исходную ветку
git checkout "$CURRENT_BRANCH" >> tmp/log_checkout.txt 2>&1

# Возвращаем stash только если он был создан
if [ "$STASH_CREATED" -eq 1 ]; then
    git stash pop >> tmp/log_checkout.txt 2>&1
fi