import os
import django

# Указываем Django, какой файл настроек использовать
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings')  # Замени flower_delivery на имя твоего проекта
print("DJANGO_SETTINGS_MODULE:", os.environ.get('DJANGO_SETTINGS_MODULE'))  # Для проверки
django.setup()


from decouple import config
import telebot
from main.models import User, Order
import requests  # Библиотека для HTTP-запросов
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from django.conf import settings  # Чтобы получать ID админа из settings.py
from django.utils.timezone import now
from main.reports import generate_text_report  # Импортируем функцию отчета
from datetime import datetime



# Токен бота
BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)


def send_telegram_message(chat_id, text):
    """Отправляет сообщение в Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    response = requests.post(url, data=payload)
    return response.json()  # Можно использовать для отладки


# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    if len(args) > 1: # Проверяем, есть ли параметры в команде
        user_id = args[1] # Получаем ID пользователя из параметра
        print("Получен user_id:", user_id)  # Для проверки user_id
        try:
            user = User.objects.get(id=user_id)
            print("Найден пользователь:", user)  # Для проверки пользователя
            user.telegram_chat_id = message.chat.id # Сохраняем Telegram ID в модели User
            user.save()
            print(f"Telegram ID {message.chat.id} сохранён для пользователя {user.username}. Проверяем в базе данных:")
            user_from_db = User.objects.get(pk=user.id)
            print(f"Проверка: Telegram ID в базе данных — {user_from_db.telegram_chat_id}")

            # Привязываем Telegram ID к заказам пользователя
            orders = Order.objects.filter(user=user)
            print(f"Найдены заказы для пользователя {user.username}: {[order.id for order in orders]}")
            for order in orders:
                order.telegram_chat_id = message.chat.id
                order.save()
                print(f"Обновлён заказ #{order.id} с telegram_chat_id {message.chat.id}")  # Для проверки

            bot.reply_to(message, "Ваш Telegram успешно привязан! Вы будете получать уведомления о заказах.")
        except User.DoesNotExist:
            print("Пользователь не найден!")
            bot.reply_to(message, "Ошибка: пользователь не найден.")
    else:
        bot.reply_to(message, f"Привет, {message.from_user.first_name}! Я бот для отслеживания заказов.")


# Команда /connect для связи Telegram ID с заказом
@bot.message_handler(commands=['connect'])
def connect_user(message):
    chat_id = message.chat.id
    username = message.from_user.username

    # Ищем последний заказ пользователя
    active_order = Order.objects.filter(user__username=username).last()
    if active_order:
        active_order.telegram_chat_id = chat_id
        active_order.save()
        bot.reply_to(message, "Ваш Telegram ID успешно связан с последним заказом!")
    else:
        bot.reply_to(message, "У вас нет активных заказов.")



# Панель администратора ---------------------------------

# ID администратора (можно хранить в settings.py)
ADMIN_TELEGRAM_ID = settings.ADMIN_TELEGRAM_ID

def is_admin(chat_id):
    """Проверяем, является ли пользователь администратором"""
    return str(chat_id) in settings.ADMIN_TELEGRAM_ID


@bot.message_handler(commands=['admin_panel'])
def admin_panel(message):
    """ Проверяем, что сообщение от администратора, и отправляем меню """
    if str(message.chat.id) != str(ADMIN_TELEGRAM_ID):
        bot.send_message(message.chat.id, "⛔ У вас нет доступа к этой панели.")
        return

    # Создаем клавиатуру с кнопками
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📊 Текстовый отчет за сегодня"))
    markup.add(KeyboardButton("💰 Выручка за сегодня"), KeyboardButton("📦 Количество заказов за сегодня"))

    bot.send_message(message.chat.id, "📢 *Панель администратора*", parse_mode="Markdown", reply_markup=markup)


# Отчет (текстовый файл) за сегодня - для Админа
@bot.message_handler(func=lambda message: message.text == "📊 Текстовый отчет за сегодня")
def send_text_report(message):
    """Генерирует и отправляет текстовый отчет за сегодня"""
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "⛔ У вас нет доступа к этой команде.")
        return

    # Генерируем текстовый отчет
    report_text = generate_text_report()
    report_path = "report_today.txt"

    with open(report_path, "w", encoding="utf-8") as file:
        file.write(report_text)

    # Отправляем файл в Телеграм
    with open(report_path, "rb") as file:
        bot.send_document(message.chat.id, file, caption="📄 Текстовый отчет за сегодня")

    os.remove(report_path)  # Удаляем файл после отправки


# Отчет Выручка за сегодня - для Админа
@bot.message_handler(func=lambda message: message.text == "💰 Выручка за сегодня")
def send_daily_revenue(message):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "⛔ У вас нет доступа к этой функции.")
        return

    # Считаем выручку за сегодня
    today = datetime.now().date()
    orders_today = Order.objects.filter(created_at__date=today)
    revenue_today = sum(order.total_price for order in orders_today)

    bot.send_message(
        message.chat.id,
        f"💰 *Выручка за сегодня:*\n{revenue_today} руб.",
        parse_mode="Markdown",
    )


# Отчет Количество заказов за сегодня - для Админа
@bot.message_handler(func=lambda message: message.text == "📦 Количество заказов за сегодня")
def send_daily_orders_count(message):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "⛔ У вас нет доступа к этой функции.")
        return

    # Считаем количество заказов за сегодня
    today = datetime.now().date()
    orders_today_count = Order.objects.filter(created_at__date=today).count()

    bot.send_message(
        message.chat.id,
        f"📦 *Количество заказов за сегодня:*\n{orders_today_count} заказ(ов).",
        parse_mode="Markdown",
    )




def main():
    print("Бот запущен...")
    bot.polling()

if __name__ == "__main__":
    main()

