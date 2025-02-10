from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.catalog, name='home'),  # Главная страница
    path('catalog/', views.catalog, name='catalog'),  # Каталог товаров
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),  # Детали товара
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'), # Добавление товара в корзину
    path('cart/', views.cart, name='cart'), # Просмотр корзины
#    path('cart/delete/<int:cart_item_id>/', views.delete_cart_item, name='delete_cart_item'), # Удаление товара из корзины
#    path('order/success/', views.order_success, name='order_success'), # Подтверждение заказа ----- ???
    path('orders/', views.user_orders, name='user_orders'), # Отображение заказов
    path('register/', views.register, name='register'), # Регистрация
    path('connect-bot/', views.connect_bot, name='connect_bot'),  # Маршрут для привязки бота
    path('login/', auth_views.LoginView.as_view(template_name='main/login.html'), name='login'), # Авторизация
    path('logout/', views.logout_user, name='logout'), # Выход из аккаунта
    path('cart/confirm/', views.confirm_order, name='confirm_order'), # Новый маршрут для подтверждения заказа
    path('cart/remove/<int:cart_item_id>/', views.delete_cart_item, name='remove_from_cart'), # Удаление товара из корзины
    path('profile/', views.profile, name='profile'), # Профиль пользователя
    path('order/finalize/', views.finalize_order, name='finalize_order'), # Финальное оформление заказа
    path("order/<int:order_id>/review/", views.leave_review, name="leave_review"), # Отзывы
    path("reports/", views.admin_reports, name="admin_reports"),  # Страница отчётов для администратора
    path("reports/download/", views.download_report, name="download_report"), # Скачивание отчета для администратора
    path("order/<int:order_id>/repeat/", views.repeat_order, name="repeat_order"), # Повторный заказ
]
