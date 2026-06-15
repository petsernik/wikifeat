@echo off
REM Переходим в каталог, где находится сам скрипт
cd /d "%~dp0"

REM === Создаем папку для временных файлов, если её нет ===
if not exist "tmp" mkdir "tmp"

REM === Запоминаем текущую ветку ===
for /f "delims=" %%i in ('git branch --show-current') do set CURRENT_BRANCH=%%i

REM === Проверяем, есть ли изменения для stash ===
set STASH_CREATED=0

git diff --quiet
if errorlevel 1 set STASH_CREATED=1

git diff --cached --quiet
if errorlevel 1 set STASH_CREATED=1

if "%STASH_CREATED%"=="1" (
    git stash push -m "auto-stash-before-script"
)

REM === Переходим на master ===
git checkout master > tmp\log_checkout.txt 2>&1

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

REM === Возвращаем исходную ветку ===
if defined CURRENT_BRANCH (
    git checkout "%CURRENT_BRANCH%" >> tmp\log_checkout.txt 2>&1
)

REM === Возвращаем stash только если он был создан ===
if "%STASH_CREATED%"=="1" (
    git stash pop >> tmp\log_checkout.txt 2>&1
)