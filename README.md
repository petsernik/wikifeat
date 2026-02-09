# Бот для автоматической публикации избранных статей Википедии в телеграм-канале
[Go to english description](#English-description)  

Ссылка на канал с публикациями: https://t.me/wikifeat.

Далее Вы можете прочитать, как воспользоваться данным кодом для публикаций в своём канале и какие ещё возможности доступны.

## Условия использования кода
Помимо условий лицензии MIT, настоятельно прошу при первом портировании, копировании, клонировании или форке 
моего проекта заменить значение переменной ```User-Agent``` в файле ```config.py```указав собственное название
проекта и ссылку. 

Например, если Ваш никнейм на GitHub это ```NickName``` и Вы сделали форк, то как вариант Вы можете указать:
```
User_Agent = 'wikifeat_fork_by_NickName/0.0 (https://github.com/NickName/wikifeat)'
```
Использование собственного ```User-Agent``` позволит избежать путаницы у волонтёров Wikimedia между 
Вашим проектом и моим. 

В случае если это правило будет нарушаться(т.е. не только я буду использовать свой User_Agent) и со стороны 
сообщества ко мне возникнут претензии, то мне придётся изменить и согласовать с волонтёрами Wikimedia новый 
```User-Agent```, а также скрыть его от публики — по аналогии с тем как сейчас скрыт токен, дающий доступ 
к управлению телеграм-ботом(т.е. через переменную окружения).  

Подобный ```User-Agent``` я использую согласно требованиям 
[Wikimedia Foundation User-Agent Policy](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy), 
без его указания в заголовке не получится запрашивать страницы напрямую с сайтов проектов Wikimedia. 
В файле ```utils.py``` уже есть готовая функция ```get_request```, которая автоматически подставляет 
```User-Agent``` из ```config.py``` в параметры заголовка.

## Первый запуск
Сперва создайте аккаунт телеграм-бота с помощью https://t.me/BotFather.

Пусть Ваш никнейм на GitHub это ```NickName``` и Вы сделали форк моего проекта, тогда:
1. Скачайте проект из своего форка или выполните клонирование:
    ```bash
    git clone https://github.com/NickName/wikifeat.git
    ```
2. Создайте и активируйте виртуальное окружение, затем установите зависимости проекта:
    ```bash
    pip install -r requirements.txt
    ```
3. Замените значение переменной ```User-Agent``` в файле ```config.py``` как указано выше:
    ```python
   User_Agent = 'wikifeat_fork_by_NickName/0.0 (https://github.com/NickName/wikifeat)'
    ```
4. Создайте переменную окружения с названием ```WIKIFEATTOKEN``` и токеном доступа к своему телеграм-боту в качестве 
значения (важно хранить данный токен в тайне от всех других).
5. В файле ```script.py``` заполните поля:
   * TELEGRAM_CHANNELS: буквенные(для публичных) или цифровые(для приватных) ID каналов или чатов, в которые Ваш 
   телеграм-бот добавлен в качестве администратора;
   * RULES_URL: ссылка на правила данного телеграм-канала, у меня 
   [CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/) на любой опубликованный ботом текст, потому что такова 
   лицензия текста на Википедии;
   * WIKI_URL: в версии 0.1 моего проекта можно указать https://ru.wikipedia.org/wiki/Заглавная_страница 
    или https://en.wikipedia.org/wiki/Main_Page, в целом несложно добавить поддержку заглавной страницы Википедии на 
    произвольном языке, главное правильно отделить блок с избранной статьёй от всего остального;
     * Дополнительно: можно указать произвольную страницу для единичного теста, например, 
     https://ru.wikipedia.org/wiki/У_омута (или статью на любом другом языке); также поддерживаются и правильно 
     обрабатываются ссылки с веб-архива, можно указать 
     https://web.archive.org/web/20211122/https://ru.wikipedia.org/wiki/Заглавная_страница и Вы получите статью избранную
     (примерно) 22 ноября 2021.
6. Запустите:
    ```bash
    python script.py
    ```
После этого в Вашем канале должен появиться пост в соответствии с выбранной ссылкой. Название заголовка опубликованной 
статьи сохраняется в файл, чтобы не публиковать одно и то же подряд при повторном запуске. Конечно можно было бы 
использовать базу данных вместо файла, но для моих нужд в этом пока нет необходимости.

## Автоматизация запусков

Данный скрипт может использоваться даже на обычном компьютере и перезапускаться автоматически даже после перезагрузки 
устройства, далее описывается как это сделать.

### Windows

Откройте планировщик задач (Win + R > taskschd.msc), нажмите "Создать задачу...", напишите название задачи, добавьте 
триггер (у меня: "однократно", повторять "каждый час", в течение "бесконечно") и действие (запуск файла ```script.vbs```;
он запускается максимально незаметно для пользователя, так что ничем не мешает), проверьте условия и параметры. 

### Linux / macOS

Для автоматизации работы можно использовать **cron** — стандартный планировщик задач в UNIX-системах.  
Рекомендуется использовать вспомогательный скрипт `script.sh`, который обновляет проект и запускает бота в фоне.

1. Убедитесь, что проект работает вручную:
   ```bash
   ./script.sh
   ```
   Если всё запускается корректно, переходите к настройке cron.

2. Сделайте файл `script.sh` исполняемым:
   ```bash
   chmod +x script.sh
   ```

3. Откройте планировщик заданий:
   ```bash
   crontab -e
   ```

4. Добавьте строку для автоматического запуска.  
   Например, чтобы бот запускался каждый час:
   ```bash
   0 * * * * /home/username/wikifeat/script.sh >/dev/null 2>&1
   ```
   Здесь:
   * `/home/username/wikifeat/` — путь к вашему проекту;  
   * `>/dev/null 2>&1` — полное подавление вывода (бот работает *тихо*, без уведомлений и терминала, аналогично 
   `script.vbs` под Windows).  

5. Проверьте, что задача добавлена:
   ```bash
   crontab -l
   ```

6. Чтобы убедиться, что всё работает, можно проверить логи:
   ```bash
   tail -n 20 /home/username/wikifeat/tmp/log.txt
   ```
   
# English description

My telegram channel with featured articles (at Russian) is https://t.me/wikifeat and I use a Telegram bot to 
automate publications.

Below is how to use my code for your channel and what other features are available. 

## Usage Terms
In addition to the MIT License Terms, please replace the `User-Agent` value in `config.py` when first porting, 
copying, cloning, or forking this project. Specify your project name and link.  

E.g. if your GitHub username is `NickName` and you forked the project:
```python
User_Agent = 'wikifeat_fork_by_NickName/0.0 (https://github.com/NickName/wikifeat)'
```
Using your own `User-Agent` helps avoid confusion for Wikimedia volunteers between your project and mine.

If this rule is violated (i.e., others use my `User-Agent`), I may need to change and coordinate a new `User-Agent` 
with Wikimedia and hide it — similar to how the Telegram bot token is kept secret via an environment variable.  

This `User-Agent` is required by the 
[Wikimedia Foundation User-Agent Policy](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy). 
Without it, direct page requests to Wikimedia projects will fail.  

The `utils.py` file contains a ready-made `get_request` function that automatically inserts the `User-Agent` from
`config.py` into request headers.

## First Launch
First of all create telegram bot account with https://t.me/BotFather. 

Assuming your GitHub username is `NickName` and you forked the project:

1. Clone your fork:
    ```bash
    git clone https://github.com/NickName/wikifeat.git
    ```
2. Create and activate a virtual environment, then install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Set the `User-Agent` in `config.py` as described above:
    ```python
   User_Agent = 'wikifeat_fork_by_NickName/0.0 (https://github.com/NickName/wikifeat)'
    ```
4. Create an environment variable `WIKIFEATTOKEN` with your Telegram bot token (keep it secret!).
5. Fill in the fields in `script.py`:
   * `TELEGRAM_CHANNELS`: letters (for public) or numbers (for private) IDs of channels or chats in which your 
   Telegram bot is added as an administrator;
   * `RULES_URL`: link to your channel’s rules. Don't forget about 
   [CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/), matching Wikipedia text licensing.
   * `WIKI_URL`: for version 0.1 you can use https://ru.wikipedia.org/wiki/Заглавная_страница or 
   https://en.wikipedia.org/wiki/Main_Page. Main pages in any other language can be added — just separate the 
   featured article block correctly.
     * Optionally, you can test with a single page, e.g., https://en.wikipedia.org/wiki/Anthony_Roll 
     (or article at any other language), or use web archive links like 
     http://web.archive.org/web/20110317042632/http://en.wikipedia.org/wiki/Main_Page to get the article as 
     featured on (roughly) that date.
6. Run it:
    ```bash
    python script.py
    ```
After this, a post with article corresponding to the selected link should appear in your channel. 
The title of this article is saved in a file .txt to prevent the same post from being published repeatedly when the 
script is run again. Of course, it would be possible to use database instead of a file, but for my needs this is not 
yet necessary.

## Automation

This script can run on an ordinary computer and be restarted automatically even after a device reboot. 
Below are instructions for each system.

### Windows

Open Task Scheduler (Win + R → `taskschd.msc`), click "Create Task…", give it a name, add a trigger (for example: 
"One time", repeat "Every hour", for "Indefinitely") and an action (run `script.vbs`).  

`script.vbs` launches `script.bat` completely silently, so it does not interfere with the user. Check all conditions 
and settings.

### Linux / macOS

For automation, use **cron**, the standard UNIX task scheduler. It is recommended to use the helper script `script.sh` 
which updates the project and runs the bot in the background.

1. Make sure the project works manually:
    ```bash
    ./script.sh
    ``` 
    If everything runs correctly, proceed to cron setup.

2. Make the script executable:
    ```bash
    chmod +x script.sh
    ```

3. Open the cron editor:
    ```bash
    crontab -e
    ```

4. Add a line for automatic execution. For example, to run the bot every hour:
    ```bash
    0 * * * * /home/username/wikifeat/script.sh >/dev/null 2>&1
    ```
    Where:
   * `/home/username/wikifeat/` — path to your project  
   * `>/dev/null 2>&1` — completely suppresses output (the bot runs silently, similar to `script.vbs` on Windows)

5. Verify the cron job:
    ```bash
    crontab -l
    ```

6. To check that it works, inspect the logs:
    ```bash
    tail -n 20 /home/username/wikifeat/tmp/log.txt
    ```
