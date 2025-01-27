from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
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
        item.total_price = item.product.price * item.quantity  # Вычисляем "Итого" для каждого товара
    total_price = sum(item.product.price * item.quantity for item in cart_items)  # Общая стоимость
    return render(request, 'main/cart.html', {'cart_items': cart_items, 'total_price': total_price})


# # Увеличение или уменьшение количества товара в корзине
# def update_cart(request, cart_item_id):
#     cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
#     action = request.POST.get('action')
#
#     if action == 'increase':
#         cart_item.quantity += 1
#     elif action == 'decrease' and cart_item.quantity > 1:
#         cart_item.quantity -= 1
#
#     cart_item.save()
#     return redirect('cart')


# Удаление товара из корзины
def delete_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
    cart_item.delete()
    return redirect('cart')

# # ОБНОВЛЕННАЯ функция удаление товара из корзины
# def remove_from_cart(request, cart_item_id):
#     if not request.user.is_authenticated:
#         return redirect('login')
#
#     cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
#     cart_item.delete()
#     messages.success(request, f"Товар {cart_item.product.name} удалён из корзины.")
#     return redirect('cart')



# # Оформление заказа
# def checkout(request):
#     if not request.user.is_authenticated:
#         return redirect('login')
#
#     cart_items = Cart.objects.filter(user=request.user)
#     if not cart_items:
#         return redirect('cart')  # Если корзина пуста, отправляем пользователя назад
#
#     if request.method == 'POST':
#         form = OrderForm(request.POST)
#         if form.is_valid():
#             # Проверяем данные пользователя в базе данных
#             user = User.objects.get(pk=request.user.pk)
#             telegram_chat_id = user.telegram_chat_id
#             print(f"Telegram ID для пользователя {user.username}: {telegram_chat_id}")
#
#             # Если Telegram ID пустой, выводим предупреждение
#             if not telegram_chat_id:
#                 print(f"Внимание! Telegram ID для пользователя {user.username} отсутствует!")
#
#
#             # Создаём заказ
#             order = Order.objects.create(
#                 user=request.user,
#                 telegram_chat_id=telegram_chat_id,  # Привязываем Telegram ID
#                 status='accepted',
#                 total_price=sum(item.product.price * item.quantity for item in cart_items)
#             )
#             print(
#                 f"Создан заказ #{order.id} для пользователя {request.user.username} с Telegram ID: {telegram_chat_id}")
#
#             order.products.set(item.product for item in cart_items)  # Связываем товары с заказом
#             order.save()
#
#             # Удаляем товары из корзины после оформления заказа
#             cart_items.delete()
#             # Перенаправляем на страницу подтверждения
#             return redirect('order_success')
#     else:
#         form = OrderForm()
#
#     return render(request, 'main/checkout.html', {'form': form, 'cart_items': cart_items})


# Новое представление, которое будет обрабатывать нажатие кнопки "Подтвердить заказ" на странице корзины
# Обработка подтверждения заказа прямо из корзины
def confirm_order(request):
    if not request.user.is_authenticated:
        return redirect('login')

    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        messages.error(request, "Ваша корзина пуста. Добавьте товары, чтобы оформить заказ.")
        return redirect('cart')

    # Проверяем Telegram ID
    user = request.user
    telegram_chat_id = user.telegram_chat_id
    if not telegram_chat_id:
        messages.error(request, "Ваш Telegram не подключён. Подключите Telegram перед оформлением заказа.")
        return redirect('cart')

    # Создаём отдельный заказ для каждого товара в корзине
    for item in cart_items:
        order = Order.objects.create(
            user=user,
            telegram_chat_id=telegram_chat_id,
            status='accepted',
            total_price=item.product.price,  # Цена одного букета
            address=item.address,
            card_text=item.card_text,
            signature=item.signature,
        )
        # Устанавливаем связь между заказом и продуктом
        order.products.set([item.product])
        order.save()

    print(f"Заказы успешно созданы для пользователя {user.username}.")

    # Очищаем корзину
    cart_items.delete()

    # Перенаправляем на страницу "Заказ оформлен"
    return redirect('order_success')


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