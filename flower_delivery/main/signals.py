from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import requests
from .models import Order
from main.utils import STATUS_TRANSLATION, generate_order_message, generate_review_button



@receiver(post_save, sender=Order)
def send_order_status_update(sender, instance, **kwargs):
    """Отправляет сообщение в Telegram при изменении статуса заказа"""
    if not instance.telegram_chat_id:
        return  # Если у пользователя нет Telegram, не отправляем сообщение

    # Исключаем статус "Принят"
    if instance.status == "accepted":
        return

    # Формируем текст сообщения
    message = generate_order_message(instance)

    # Генерируем кнопку, если нужно
    reply_markup = generate_review_button(instance)

    # Формируем payload для отправки сообщения
    payload = {
        "chat_id": instance.telegram_chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    # Отправляем сообщение через Telegram API
    telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(telegram_url, json=payload)

