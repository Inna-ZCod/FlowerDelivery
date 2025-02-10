from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import login, logout, update_session_auth_hash
from .forms import UserRegistrationForm, ReviewForm
from .models import Product, Cart, Order, Review
from django import template
from telegram_bot import send_telegram_message
from django.db import models
from django.utils.timezone import now, timedelta
from django.http import HttpResponse
from main.reports import generate_text_report
from main.utils import STATUS_TRANSLATION, generate_card_info, send_order_notification


# функции для извлечения текста открытки и подписи
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


def catalog(request):
    products = Product.objects.all()
    return render(request, 'main/catalog.html', {'products': products})


# ---------------Пользователь-------------------------------

# обработчик для регистрации
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('connect_bot')  # Перенаправляем на привязку Telegram
    else:
        form = UserRegistrationForm()
    return render(request, 'main/register.html', {'form': form})


#  перенаправляем пользователя на страницу с кнопкой для привязки бота
def connect_bot(request):
    return render(request, 'main/connect_bot.html')


# Выход пользователя из аккаунта
def logout_user(request):
    logout(request)  # Завершаем сессию пользователя
    return redirect('home')  # Перенаправляем на главную


# Профиль пользователя
def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')

    password_form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and password_form.is_valid():
        password_form.save()
        update_session_auth_hash(request, password_form.user)  # Чтобы не разлогинивало
        messages.success(request, "Пароль успешно изменён.")
        return redirect('profile')

    return render(request, 'main/profile.html', {'password_form': password_form})

# ------------- Корзина -----------------

# Один продукт = один букет
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)  # Получаем товар по ID или возвращаем 404
    reviews = Review.objects.filter(product=product).order_by('-created_at')  # ✅ Берем все отзывы, а не только текущего пользователя
    return render(request, 'main/product_detail.html', {"product": product, "reviews": reviews})


# Функция для добавления в корзину
def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)

    # Если пользователь не авторизован, перенаправляем на страницу логина
    if not request.user.is_authenticated:
        return redirect('login')

    # Создаём новую запись в корзине для каждого добавления
    Cart.objects.create(
        user=request.user,
        product=product
    )

    # Перенаправляем обратно на ту же страницу, где был пользователь
    return redirect(request.META.get('HTTP_REFERER', 'catalog'))


# Отображение корзины
def cart(request):
    if not request.user.is_authenticated:
        return redirect('login')

    cart_items = Cart.objects.filter(user=request.user)  # Получаем товары в корзине
    for item in cart_items:
        item.total_price = item.product.price  # "Итого" для каждой позиции — это цена самого товара
    total_price = sum(item.product.price for item in cart_items)  # Общая стоимость корзины
    return render(request, 'main/cart.html', {'cart_items': cart_items, 'total_price': total_price})


# Удаление товара из корзины
def delete_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
    cart_item.delete()
    return redirect('cart')


# -------------- Заказы ----------------------

# Отображение списка заказов на странице "Мои заказы"
def user_orders(request):
    if not request.user.is_authenticated:
        return redirect('login')

    orders = Order.objects.filter(user=request.user).select_related("review").order_by('-created_at')

    # Подготовка структуры для хранения отформатированных данных заказов
    formatted_orders = []
    for order in orders:
        # Формируем корректное сообщение об открытке
        card_info = generate_card_info(order.card_text, order.signature)

        formatted_orders.append({
            "order_id": order.id,
            "status": STATUS_TRANSLATION.get(order.status, order.status),  # Переводим статус
            "created_at": order.created_at.strftime("%d.%m.%Y %H:%M"),  # Форматируем дату
            "bouquet_name": order.products.first().name if order.products.exists() else "Не указан",  # Название букета
            "delivery_address": order.address if order.address else "Адрес не указан",
            "card_info": card_info,  # Открытка и подпись
            "price": order.total_price,  # Цена
            "has_review": hasattr(order, "review")  # Проверяем, есть ли у заказа отзыв
        })

    return render(request, 'main/orders.html', {'orders': formatted_orders})


# Обработка подтверждения заказа из корзины при нажатии кнопки "Подтвердить заказ"
def confirm_order(request):
    if not request.user.is_authenticated:
        return redirect('login')

    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        messages.error(request, "Ваша корзина пуста. Добавьте товары, чтобы оформить заказ.")
        return redirect('cart')

    # Проверяем, есть ли пустые адреса
    if request.method == "POST":
        missing_addresses = [item for item in cart_items if not request.POST.get(f"address_{item.id}", "").strip()]
        if missing_addresses:
            messages.warning(request, "Укажите адрес доставки для всех товаров в корзине.")
            return redirect('cart')

        # ✅ Сохраняем введенные данные в Cart
        for item in cart_items:
            item.address = request.POST.get(f"address_{item.id}", "").strip()
            item.card_text = request.POST.get(f"card_text_{item.id}", "").strip()
            item.signature = request.POST.get(f"signature_{item.id}", "").strip()
            item.save()

    # ✅ Формируем структуру заказа для отображения на странице подтверждения
    order_summary = []
    for item in cart_items:
        address = item.address  # Теперь берем из Cart, а не из POST
        text = item.card_text
        signature = item.signature

        # Логика формирования текста открытки
        card_info = generate_card_info(text, signature)

        order_summary.append({
            "bouquet_name": item.product.name,
            "delivery_address": address,
            "card_info": card_info,  # ✅ Теперь передаем список пар
            "price": item.product.price,
        })

    return render(request, "main/cart_confirm.html", {
        "order_summary": order_summary,
        "total_price": sum(item.product.price for item in cart_items),
    })


# Финальное оформление заказа
def finalize_order(request):
    if not request.user.is_authenticated:
        return redirect('login')

    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        messages.error(request, "Ваша корзина пуста. Добавьте товары, чтобы оформить заказ.")
        return redirect('cart')

    user = request.user
    telegram_chat_id = user.telegram_chat_id

    for item in cart_items:
        order = Order.objects.create(
            user=user,
            telegram_chat_id=telegram_chat_id,
            status='accepted',
            total_price=item.product.price,
            address=item.address,  # ✅ Теперь берем данные из Cart!
            card_text=item.card_text,
            signature=item.signature,
        )

        # Сохраняем заказ
        order.products.set([item.product])
        order.save()

        if telegram_chat_id:
            header = f"🛍 *Ваш заказ №{order.id} подтверждён!*\n\n"
            message_text = header + send_order_notification(order)
            message_text += "------------------------\n🌸 Ожидайте дальнейшей информации о статусе заказа!"
            send_telegram_message(telegram_chat_id, message_text)

        # -------------------------------

    cart_items.delete()  # ✅ Очищаем корзину

    return redirect('user_orders')  # Перенаправляем на "Мои заказы"


# -------------- Отзывы ---------------------------------------

# Отзывы - обработка формы для отзыва
@login_required
def leave_review(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Проверяем, есть ли уже отзыв к этому заказу
    if hasattr(order, "review"):
        return redirect("product_detail", product_id=order.products.first().id)  # Если отзыв уже есть, возвращаем в заказы

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = order.products.first()  # Связываем с продуктом
            review.order = order  # Связываем с заказом
            review.save()
            return redirect("product_detail", product_id=order.products.first().id)  # Перенаправляем на страницу букета
    else:
        form = ReviewForm()

    return render(request, "main/leave_review.html", {"form": form, "order": order})


# Повторный заказ
@login_required
def repeat_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Создаем новые элементы в корзине
    for product in order.products.all():
        Cart.objects.create(
            user=request.user,
            product=product,
            address=order.address,
            card_text=order.card_text,
            signature=order.signature,
        )

    messages.success(request, "Товары из заказа добавлены в корзину!")
    return redirect("cart")


# ------------ Отчеты для администратора -------------------------

# Декоратор, чтобы доступ был только у админа
def admin_required(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(admin_required)
def admin_reports(request):
    if not request.user.is_superuser:
        return redirect("home")  # Доступ только для админа

    total_orders = Order.objects.count()  # Отчет: Общее количество заказов

    # Отчет: Количество заказов по статусам
    status_counts = Order.objects.values("status").annotate(count=models.Count("id"))

    # Формируем удобную структуру
    orders_by_status = {
        STATUS_TRANSLATION[entry["status"]]: entry["count"] for entry in status_counts
    }

    # Отчет: Количество заказов, оформленных каждым пользователем
    user_orders_count = Order.objects.values("user__username").annotate(total=models.Count("id")).order_by("-total")

    # Отчет: Самые популярные букеты
    popular_bouquets = (
        Order.objects.values("products__name")
        .annotate(total=models.Count("products"))
        .order_by("-total")[:5]  # Топ-5 самых популярных букетов
    )

    # Отчет: Рассчитываем средний чек заказов
    average_order_value = Order.objects.aggregate(avg_price=models.Avg("total_price"))["avg_price"] or 0


    # Отчет: Общая сумма выручки за день/неделю/месяц
    # Дата сегодня
    today = now().date()

    # Фильтрация заказов по дате
    revenue_today = Order.objects.filter(created_at__date=today).aggregate(total=models.Sum("total_price"))[
                        "total"] or 0
    revenue_week = \
    Order.objects.filter(created_at__gte=today - timedelta(days=7)).aggregate(total=models.Sum("total_price"))[
        "total"] or 0
    revenue_month = \
    Order.objects.filter(created_at__gte=today - timedelta(days=30)).aggregate(total=models.Sum("total_price"))[
        "total"] or 0


    return render(request, "main/admin_reports.html", {
        "total_orders": total_orders,
        "orders_by_status": orders_by_status,
        "user_orders_count": user_orders_count,
        "popular_bouquets": popular_bouquets,
        "average_order_value": average_order_value,
        "revenue_today": revenue_today,  # ✅ Выручка за сегодня
        "revenue_week": revenue_week,    # ✅ Выручка за неделю
        "revenue_month": revenue_month,  # ✅ Выручка за месяц
    })


# Скачивание отчетов администратора
def download_report(request):
    if not request.user.is_staff:
        return HttpResponse("У вас нет доступа к этому отчету.", status=403)

    """Генерирует текстовый отчет и отправляет его в виде файла."""
    report_content = generate_text_report()

    # Создаем HTTP-ответ с файлом
    response = HttpResponse(report_content, content_type="text/plain")
    response["Content-Disposition"] = "attachment; filename=order_report.txt"
    return response