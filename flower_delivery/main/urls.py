from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Главная страница
    path('catalog/', views.catalog, name='catalog'),  # Каталог товаров
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),  # Детали товара
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'), # Добавление товара в корзину
    path('cart/', views.cart, name='cart'), # Просмотр корзины
    path('checkout/', views.checkout, name='checkout'), # Оформление заказа
    path('order/success/', views.order_success, name='order_success'), # Подтверждение заказа
]
