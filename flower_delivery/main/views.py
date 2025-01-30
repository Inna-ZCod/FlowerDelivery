from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import login, logout, update_session_auth_hash
from .forms import OrderForm, UserRegistrationForm
from .models import Product, Cart, Order



def catalog(request):
    products = Product.objects.all()
    return render(request, 'main/catalog.html', {'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)  # Получаем товар по ID или возвращаем 404
    return render(request, 'main/product_detail.html', {'product': product})


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




# Новое представление, которое будет обрабатывать нажатие кнопки "Подтвердить заказ" на странице корзины
# Обработка подтверждения заказа прямо из корзины
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

    # Формируем структуру заказа
    order_summary = []
    for item in cart_items:
        address = request.POST.get(f"address_{item.id}", "").strip()
        text = request.POST.get(f"card_text_{item.id}", "").strip()
        signature = request.POST.get(f"signature_{item.id}", "").strip()

        # Логика формирования текста открытки
        if text and signature:
            card_info = [
                ("Текст на открытке:", text),
                ("Подпись:", signature)
            ]
        elif text:
            card_info = [
                ("Текст на открытке:", text),
                ("Подпись:", "Без подписи")
            ]
        elif signature:
            card_info = [
                ("Текст на открытке:", signature)  # Подпись становится текстом на открытке
            ]
        else:
            card_info = [
                ("Текст на открытке:", "Без открытки")
            ]

        order_summary.append({
            "bouquet_name": item.product.name,
            "delivery_address": address,
            "card_info": card_info,  # Теперь передаем список пар
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

    if request.method == "POST":
        user = request.user
        telegram_chat_id = user.telegram_chat_id

        for item in cart_items:
            order = Order.objects.create(
                user=user,
                telegram_chat_id=telegram_chat_id,
                status='accepted',
                total_price=item.product.price,
                address=item.address,
                card_text=item.card_text,
                signature=item.signature,
            )
            order.products.set([item.product])
            order.save()

        # Очищаем корзину
        cart_items.delete()

        # Перенаправляем пользователя на "Мои заказы"
        return redirect('user_orders')

    return redirect('cart')



# Подтвердение заказа
def order_success(request):
    return render(request, 'main/order_success.html')


# Отображение списка заказов
def user_orders(request):
    if not request.user.is_authenticated:
        return redirect('login')

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'main/orders.html', {'orders': orders})


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