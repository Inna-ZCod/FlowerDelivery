#
# Общий модуль для хранения повторяющихся фрагментов кода
# -------------------------------------------------------
#

from django.conf import settings
from .models import Review



# Перевод статусов на русский язык
STATUS_TRANSLATION = {
    "accepted": "Принят",
    "assembling": "В сборке",
    "on_the_way": "В пути",
    "delivered": "Доставлен"
}


# Логика формирования текста на открытке
def generate_card_info(text, signature):
    if text and signature:
        return [
            ("Текст на открытке:", text),
            ("Подпись:", signature)
        ]
    elif text:
        return [
            ("Текст на открытке:", text),
            ("Подпись:", "Без подписи")
        ]
    elif signature:
        return [
            ("Текст на открытке:", signature)  # Подпись становится текстом на открытке
        ]
    else:
        return [
            ("Текст на открытке:", "Без открытки")
        ]


def send_order_notification(order):
    """
    Формирует основную часть уведомления о заказе.
    :param order: Объект заказа
    :return: Текст сообщения
    """
    message_text = f"🌸 *Букет:* {order.products.first().name if order.products.exists() else 'Не указан'}\n"
    message_text += f"📍 *Адрес доставки:* {order.address if order.address else 'Не указан'}\n"

    # Формируем части открытки
    card_info = generate_card_info(order.card_text, order.signature)
    for label, value in card_info:
        message_text += f"{label} {value}\n"

    message_text += f"💰 *Цена:* {order.total_price} руб.\n"
    message_text += f"📅 *Дата заказа:* {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"

    return message_text



def generate_order_message(order):
    """Генерирует текстовое сообщение о заказе"""
    translated_status = STATUS_TRANSLATION.get(order.status, order.status)
    return (
        f"📢 Обновление статуса заказа №{order.id}!\n\n"
        f"🔄 Новый статус: *{translated_status}*\n"
        f"📅 Дата заказа: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"💐 Букет: {order.products.first().name if order.products.exists() else 'Не указан'}\n"
        f"📍 Адрес доставки: {order.address}\n"
        f"💰 Цена: {order.total_price} руб."
    )


def generate_review_button(order):
    """Генерирует кнопку для оставления отзыва, если заказ доставлен"""
    if order.status != "delivered":
        return None

    review_exists = Review.objects.filter(order=order).exists()

    if review_exists:
        review_url = f"{settings.SITE_URL}/product/{order.products.first().id}/"
        button_text = "🌟 Посмотреть отзывы"
    else:
        review_url = f"{settings.SITE_URL}/order/{order.id}/review/"
        button_text = "📝 Оставить отзыв"

    return {"inline_keyboard": [[{"text": button_text, "url": review_url}]]}