#
# Общий модуль для хранения повторяющихся фрагментов кода
# -------------------------------------------------------
#


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