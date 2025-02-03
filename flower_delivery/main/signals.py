from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.conf import settings
import requests
from .models import Order, Review

import logging
# Настраиваем логирование
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
SITE_URL = settings.SITE_URL


@receiver(post_save, sender=Order)
def send_order_status_update(sender, instance, **kwargs):
    logger.info(f"📌 Отладка: Обработка заказа #{instance.id}")
    """Отправляет сообщение в Telegram при изменении статуса заказа"""
    if not instance.telegram_chat_id:
        logger.warning(f"⚠ У заказа #{instance.id} нет Telegram ID, сообщение не отправлено.")
        return  # Если у пользователя нет Telegram, не отправляем сообщение

    # Перевод статусов
    status_translation = {
        "accepted": "Принят",
        "assembling": "В сборке",
        "on_the_way": "В пути",
        "delivered": "Доставлен"
    }

    translated_status = status_translation.get(instance.status, instance.status)
    logger.info(f"🔍 Отладка: текущий статус заказа #{instance.id}: {translated_status}")

    # Если статус не "В сборке", "В пути" или "Доставлен" — выходим
    if instance.status == "accepted":
        logger.warning(f"⚠ Статус заказа #{instance.id} ({translated_status}) не требует отправки сообщения.")
        return

    # Формируем текст сообщения
    message = (
        f"📢 Обновление статуса заказа №{instance.id}!\n\n"
        f"🔄 Новый статус: *{translated_status}*\n"
        f"📅 Дата заказа: {instance.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"💐 Букет: {instance.products.first().name if instance.products.exists() else 'Не указан'}\n"
        f"📍 Адрес доставки: {instance.address}\n"
        f"💰 Цена: {instance.total_price} руб."
    )

    logger.info(f"📨 Готовим отправку сообщения для заказа #{instance.id}:\n{message}")

    # ✅ Проверяем, оставлен ли уже отзыв
    review_exists = Review.objects.filter(order=instance).exists()

    # ✅ Логика добавления кнопки Оставить отзыв
    reply_markup = None
    if instance.status == "delivered":  # Только если заказ доставлен
        if review_exists:
            review_url = f"{settings.SITE_URL}/product/{instance.products.first().id}/"  # Ведём на страницу товара
            button_text = "🌟 Посмотреть отзывы"
        else:
            review_url = f"{settings.SITE_URL}/order/{instance.id}/review/"  # Ведём на форму отзыва
            button_text = "📝 Оставить отзыв"

        reply_markup = {
            "inline_keyboard": [[{"text": button_text, "url": review_url}]]
        }
        logger.info(f"✅ К заказу #{instance.id} добавлена кнопка 'Оставить отзыв'")

    # Формируем payload без параметра reply_markup, если он не нужен
    payload = {
        "chat_id": instance.telegram_chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    # Добавляем reply_markup, если он есть
    if reply_markup:
        payload["reply_markup"] = reply_markup

    # Отправляем сообщение через Telegram API
    telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(telegram_url, json=payload)

    # ✅ Логируем ответ от Telegram API
    logger.info(f"📨 Ответ Telegram API для заказа #{instance.id}: {response.text}")