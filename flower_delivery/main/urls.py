from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),  # Главная страница
    path('catalog/', views.catalog, name='catalog'),  # Каталог товаров
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),  # Детали товара
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'), # Добавление товара в корзину
    path('cart/', views.cart, name='cart'), # Просмотр корзины
    path('checkout/', views.checkout, name='checkout'), # Оформление заказа
    path('cart/update/<int:cart_item_id>/', views.update_cart, name='update_cart'),
    path('cart/delete/<int:cart_item_id>/', views.delete_cart_item, name='delete_cart_item'),
    path('order/success/', views.order_success, name='order_success'), # Подтверждение заказа
    path('orders/', views.user_orders, name='user_orders'), # Отображение заказов
    path('register/', views.register, name='register'), # Регистрация
    path('connect-bot/', views.connect_bot, name='connect_bot'),  # Маршрут для привязки бота
    path('login/', auth_views.LoginView.as_view(template_name='main/login.html'), name='login'), # Авторизация
    path('logout/', views.logout_user, name='logout'), # Выход из аккаунта
]
