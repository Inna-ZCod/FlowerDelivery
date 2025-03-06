# FlowerDelivery


## Описание

**FlowerDelivery** – это веб-приложение для оформления и отслеживания заказов на доставку цветов. Сервис позволяет пользователям:

- Просматривать каталог букетов.
- Добавлять букеты в корзину.
- Добавлять открытки к букетам.
- Оформлять заказы.
- Отслеживать статус заказов.
- Оставлять отзывы.

Администратор получает доступ к аналитике и отчетам о заказах, а также может управлять статусами заказов.

## Скриншоты
**Статус заказа с возможностью оставить отзыв и повторить заказ**
<img src="https://raw.githubusercontent.com/Inna-ZCod/FlowerDelivery/main/flower_delivery/media/products/fd_03.png" alt="Статус заказа" width="400">

**Функционал добавления открытки к букету**
<img src="https://raw.githubusercontent.com/Inna-ZCod/FlowerDelivery/main/flower_delivery/media/products/fd_04.png" alt="Добавление открытки" width="400">

**Отчеты администратора** (доступны только для аккаунта администратора)
<img src="https://raw.githubusercontent.com/Inna-ZCod/FlowerDelivery/main/flower_delivery/media/products/fd_05.png" alt="Отчеты администратора" width="400">



## Технологии

- Python 3.10
- Django 5.1
- PostgreSQL
- Bootstrap
- Telebot (для интеграции с Telegram-ботом)
- Pytest (для тестирования)


## Установка

1. Клонируйте репозиторий:

   ```
   git clone https://github.com/Inna-ZCod/FlowerDelivery.git
   ```

2. Перейдите в папку проекта:

   ```
   cd FlowerDelivery
   ```

3. Создайте и активируйте виртуальное окружение:

   ```
   python -m venv venv
   source venv/bin/activate  # Для Linux/MacOS
   venv\Scripts\activate  # Для Windows
   ```

4. Установите зависимости:

   ```
   pip install -r requirements.txt
   ```

5. Выполните миграции базы данных:

   ```
   python manage.py migrate
   ```

6. Создайте суперпользователя (для входа в админ-панель):

   ```
   python manage.py createsuperuser
   ```

7. Запустите сервер разработки:

   ```
   python manage.py runserver
   ```

8. Запустите телеграм-бот:

   ```
   python telegram_bot.py
   ```


## Использование

1. Откройте браузер и перейдите по адресу http://127.0.0.1:8000/.

2. Зарегистрируйтесь или войдите в систему.

3. Выберите букет, добавьте его в корзину и оформите заказ.

4. К каждому букету можно добавить открытку с поздравлением и подписью.

5. Подключите Telegram-бота, чтобы получать уведомления о статусе заказа.

6. После того, как заказ получет статус "Доставлен", появится возможность оставить отзыв о нем.

7. Администратор имеет дополнительный функционал в виде отчетов на сайте. Также он может получать отчеты в Telegram-бот.


## Тестирование

Для запуска тестов выполните команду:

   ```
   pytest main/tests/
   ```


## Структура проекта

- main/ – основное приложение Django.

- templates/main/ – HTML-шаблоны.

- static/ – файлы стилей и скрипты.

- media/ – загруженные изображения товаров.

- telegram_bot.py – обработчик команд Telegram-бота.

- utils.py – вспомогательные функции.


## Авторы

Проект разработан с любовью и вниманием ❤️.


## Лицензия

Этот проект распространяется под лицензией **MIT**.
