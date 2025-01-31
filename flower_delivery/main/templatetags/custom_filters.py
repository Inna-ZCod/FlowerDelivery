from django import template

register = template.Library()

@register.filter
def get_card_text(card_info):
    """Извлекает текст на открытке, если он есть"""
    for label, value in card_info:
        if label == "Текст на открытке:":
            return value
    return ""

@register.filter
def get_signature(card_info):
    """Извлекает подпись, если она есть"""
    for label, value in card_info:
        if label == "Подпись:":
            return value
    return ""