from .models import Cart
from django.db.models import Sum

def get_cart_item_count(user):
    """Возвращает общее количество товаров в корзине пользователя."""
    return Cart.objects.filter(user=user).aggregate(Sum('quantity'))['quantity__sum'] or 0

def cart_item_count(request):
    """Добавляет количество товаров в корзине в контекст шаблонов."""
    if request.user.is_authenticated:
        return {'cart_item_count': get_cart_item_count(request.user)}
    return {'cart_item_count': 0}