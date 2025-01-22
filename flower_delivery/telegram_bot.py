from decouple import config
import telebot

# Токен бота
BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")

# Создаём экземпляр бота
bot = telebot.TeleBot(BOT_TOKEN)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"Привет, {message.from_user.first_name}! Я бот для отслеживания заказов.")

# Основная функция
def main():
    print("Бот запущен...")
    bot.polling()

if __name__ == "__main__":
    main()

