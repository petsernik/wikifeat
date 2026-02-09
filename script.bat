@echo off
REM Переходим в каталог, где находится сам скрипт
cd /d "%~dp0"

REM === Создаем папку для временных файлов, если её нет ===
if not exist "tmp" mkdir "tmp"

REM === Обновляем проект ===
(
  echo [%date% %time%] Starting update...
  git pull
) > tmp\log_git.txt 2>&1

REM === Активируем виртуальное окружение (если есть), устанавливаем зависимости и запускаем Python ===
(
  if exist ".venv\Scripts\activate.bat" (
    echo [%date% %time%] Virtual environment found. Activating...
    call .venv\Scripts\activate.bat
  ) else (
    echo [%date% %time%] No virtual environment found. Running without it.
  )

  echo [%date% %time%] Check and install requirements...
  pip install -r requirements.txt
  echo [%date% %time%] Running script.py...
  python script.py
  echo [%date% %time%] Script finished.
) > tmp\log.txt 2>&1
