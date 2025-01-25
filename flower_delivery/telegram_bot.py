import os
import django

# Указываем Django, какой файл настроек использовать
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings')  # Замени flower_delivery на имя твоего проекта
print("DJANGO_SETTINGS_MODULE:", os.environ.get('DJANGO_SETTINGS_MODULE'))  # Для проверки
django.setup()


from decouple import config
import telebot
from main.models import User, Order


# Токен бота
BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)


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


def main():
    print("Бот запущен...")
    bot.polling()

if __name__ == "__main__":
    main()

