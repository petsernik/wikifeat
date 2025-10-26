#!/bin/bash
# Переходим в каталог, где находится сам скрипт
cd "$(dirname "$0")" || exit 1

# Обновляем проект
{
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting update..."
  git pull
} > log_git.txt 2>&1

# Активируем виртуальное окружение (если есть) и запускаем Python-скрипт
{
  if [ -f ".venv/bin/activate" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Virtual environment found. Activating..."
    source .venv/bin/activate
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] No virtual environment found. Running without it."
  fi

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running script.py..."
  python script.py
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Script finished."
} > log.txt 2>&1
