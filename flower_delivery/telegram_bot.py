import os
import django

# Указываем Django, какой файл настроек использовать
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings')  
print("DJANGO_SETTINGS_MODULE:", os.environ.get('DJANGO_SETTINGS_MODULE'))  # Для проверки
django.setup()


import telebot
import requests  # Библиотека для HTTP-запросов
from decouple import config
from main.models import User, Order
from main.reports import generate_text_report  # Импортируем функцию отчета
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from django.conf import settings  # Чтобы получать ID админа из settings.py
from django.urls import reverse
from datetime import datetime



# Токен бота
BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
MY_SITE = config("SITE_URL")
ADMIN_TELEGRAM_ID = settings.ADMIN_TELEGRAM_ID


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
        try:
            user = User.objects.get(id=user_id)
            user.telegram_chat_id = message.chat.id # Сохраняем Telegram ID в модели User
            user.save()
            user_from_db = User.objects.get(pk=user.id)

            # Привязываем Telegram ID к заказам пользователя
            orders = Order.objects.filter(user=user)
            for order in orders:
                order.telegram_chat_id = message.chat.id
                order.save()

            bot.reply_to(message, "Ваш Telegram успешно привязан! Вы будете получать уведомления о заказах.")
        except User.DoesNotExist:
            bot.reply_to(message, "Ошибка: пользователь не найден.")



    if str(message.chat.id) == ADMIN_TELEGRAM_ID:
        # Если админ, отправляем его сразу в панель администратора
        admin_panel(message)
    else:
        # Если обычный пользователь, отправляем стандартное пользовательское меню
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("🌐 Перейти на сайт"), KeyboardButton("📦 Мои заказы"))
        bot.send_message(
            message.chat.id,
            "👋 Добро пожаловать в FlowerDelivery! Здесь вы можете отслеживать свои заказы и переходить на наш сайт.",
            reply_markup=markup,
        )


# Кнопка Перейти на сайт - для пользователя
@bot.message_handler(func=lambda message: message.text == "🌐 Перейти на сайт")
def go_to_site(message):
    bot.send_message(
        message.chat.id,
        f"🌐 Вот ссылка на наш сайт:\n[Перейти на сайт]({MY_SITE})",
        parse_mode="Markdown",
    )


# Кнопка Мои заказы - для пользователя
@bot.message_handler(func=lambda message: message.text == "📦 Мои заказы")
def my_orders(message):
    user = User.objects.filter(telegram_chat_id=message.chat.id).first()

    if not user:
        bot.send_message(message.chat.id, "❌ Вы не зарегистрированы на сайте. Пожалуйста, зарегистрируйтесь.")
        return

    orders = Order.objects.filter(user=user).order_by('-created_at')[:5]

    if not orders.exists():
        bot.send_message(message.chat.id, "📭 У вас пока нет заказов.")
        return

    # Формируем текст сообщения
    orders_message = "📦 *Ваши последние заказы:*\n\n"

    for order in orders:
        orders_message += f"🔹 *Заказ №{order.id}*\n"
        orders_message += f"📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        orders_message += f"🔄 Статус: {order.get_status_display()}\n"
        orders_message += f"💐 Букет: {order.products.first().name if order.products.exists() else 'Не указан'}\n"

        # Ссылка для отзыва, если статус "Доставлен" и отзыв не оставлен
        if order.status == "delivered" and not hasattr(order, "review"):
            review_url = f"{MY_SITE}{reverse('leave_review', args=[order.id])}"
            orders_message += f"📝 [Оставить отзыв]({review_url})\n"

        # Ссылка для повторного заказа
        reorder_url = f"{MY_SITE}{reverse('product_detail', args=[order.products.first().id])}"
        orders_message += f"🔄 [Повторить заказ]({reorder_url})\n"

        orders_message += "------------------------\n"

    # Добавляем ссылку на сайт
    orders_message += f"\n🌐 [Посмотреть все заказы]({MY_SITE}/orders/)"

    bot.send_message(
        message.chat.id,
        orders_message,
        parse_mode="Markdown"
    )




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



# ----------- Панель администратора ---------------------------------

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

