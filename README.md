# Бот для автоматической публикации избранных статей Википедии в телеграм-канале
[Go to english description](#English-description)  

Ссылка на канал с публикациями: https://t.me/wikifeat.

Далее Вы можете прочитать как запустить данный проект для публикаций в Вашем собственном канале, 
а также узнать какой дополнительный (опциональный) функционал предоставляется проектом (мультиязычность, 
возможность работы с конкретной статьёй, поддержка ссылок из web.archive.org).

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
значения (важно хранить данный токен в тайне от всех других). После этого может понадобиться перезагрузка устройства.
5. В файле ```script.py``` заполните поля:
   * TELEGRAM_CHANNELS: буквенные(для публичных) или цифровые(для приватных) ID каналов или чатов, в которые Ваш 
   телеграм-бот добавлен в качестве администратора;
   * RULES_URL: ссылка на правила данного телеграм-канала, у меня 
   [CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/) на любой опубликованный ботом текст, потому что такова 
   лицензия текста на Википедии;
   * LANG_CODE: код языка по стандарту [ISO 639-1](https://ru.wikipedia.org/wiki/Список_кодов_ISO_639-1)
     (ru, en, и т.д.)
   * WIKI_URL: в версии 0.31 моего проекта можно указать "Шаблон:Текущая избранная статья" 
    или "Wikipedia:Today's featured article", в целом несложно добавить поддержку шаблона на 
    произвольном языке, главное правильно отделить блок с избранной статьёй от всего остального. Также можно указать:
     * заглавную страницу в явном виде ("Заглавная страница", 
     "Main Page", "Wikipédia:Accueil principal", ...), но не рекомендуется, так как они могут отображать
     более старые данные, чем указанные ранее шаблоны (при отсутствии авторизованного входа в аккаунт на Википедии,
     например, через режим инкогнито);
     * на данный момент поддерживаются такие значения заглавной страницы: "Заглавная страница, Main Page, Wikipédia:Accueil principal, Wikipedia:Hauptseite, Wikipedia:Portada, Pagina principale, Wikipédia:Página_principal, Wikipedia:Strona główna, Галоўная старонка, Басты бет".
     Можно сразу использовать TRANSLATIONS[LANG_CODE][TKey.MAIN_PAGE] из файла i18n.py, а не писать вручную.
     * произвольную страницу для единичного теста, например, "У омута" (статью можно указывать на любом языке);
     * ссылку можно ввести полноценно, например, https://ru.wikipedia.org/wiki/Заглавная_страница
     или https://ru.wikipedia.org/wiki/У_омута; также поддерживаются и правильно 
     обрабатываются ссылки с веб-архива, можно указать 
     https://web.archive.org/web/20211122/https://ru.wikipedia.org/wiki/Заглавная_страница и Вы получите статью
     избранную (примерно) 22 ноября 2021.
   * остальные параметры можно не менять.
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
триггер (у меня: "однократно", повторять "каждый час", в течение "бесконечно") и действие (запуск файла ```script.vbs```,
обязательно укажите рабочую директорию(репозиторий на вашем локальном диске, например, C:\...\wikifeat), 
иначе задача не сможет выполниться корректно; ```script.vbs``` запускается максимально незаметно для пользователя, 
так что ничем не мешает), проверьте условия и параметры.

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

Below you can read how to run this project for publishing in your own channel, 
as well as learn about the additional (optional) features provided by the project 
(multilingual support, the ability to work with a specific article, and support for links from web.archive.org).

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
4. Create an environment variable `WIKIFEATTOKEN` with your Telegram bot token (keep it secret!). After that you
may need to reboot the OS.
5. Fill in the fields in `script.py`:
   * `TELEGRAM_CHANNELS`: letters (for public) or numbers (for private) IDs of channels or chats in which your 
   Telegram bot is added as an administrator;
   * `RULES_URL`: link to your channel’s rules. Don't forget about 
   [CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/), matching Wikipedia text licensing.
   * `LANG_CODE`: language code according to the [ISO 639-1 standard](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) 
      (ru, en, etc.);
   * `WIKI_URL`: in version 0.31 of the project you can specify
     "Шаблон:Текущая избранная статья" or "Wikipedia:Today's featured article".
     In general, it is not difficult to add support for templates in any language —
     the main task is to correctly extract the featured article block from the rest
     of the page. You can also specify:
     * the main page explicitly ("Заглавная страница" or "Main Page"), but this is not
       recommended, as it may display older data than the templates mentioned above
       (for example, when not logged into a Wikipedia account, such as in incognito
       mode);
     * currently supported values for the main page are: "Заглавная страница, Main Page, Wikipédia:Accueil principal, Wikipedia:Hauptseite, Wikipedia:Portada, Pagina principale, Wikipédia:Página_principal, Wikipedia:Strona główna, Галоўная старонка, Басты бет".
       You can use TRANSLATIONS[LANG_CODE][TKey.MAIN_PAGE] from the i18n.py file instead of specifying it manually.
     * an arbitrary page for a single test, for example "Anthony Roll" (the article can be specified in any language);
     * a full URL, for example https://en.wikipedia.org/wiki/Main_Page or
       https://en.wikipedia.org/wiki/Anthony_Roll; web archive links are also
       supported and processed correctly. For example,
       http://web.archive.org/web/20110317042632/http://en.wikipedia.org/wiki/Main_Page
       will return the article featured (approximately) on that date;
   * other parameters can be left unchanged.
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

Open Task Scheduler (Win + R → `taskschd.msc`), click **"Create Task…"**, give it a name, add a trigger (for example:  
"One time", repeat "Every hour", for **"Indefinitely"**) and an action (run `script.vbs`).  

Make sure to **set the "Start in" (working directory)** to the local repository folder (for example, `C:\...\wikifeat`), 
otherwise the task may not run correctly.  

`script.vbs` launches `script.bat` completely silently, so it does not interfere with the user. 
Review all **conditions** and **settings** to ensure the task runs reliably.

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
