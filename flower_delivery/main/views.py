from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from .forms import OrderForm, UserRegistrationForm
from .models import Product, Cart, Order


def home(request):
    return render(request, 'main/home.html')

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
    # Если пользователь не авторизован, можно перекинуть его на страницу логина
    if not request.user.is_authenticated:
        return redirect('login')

    # Проверяем, есть ли уже такой товар в корзине пользователя
    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product
    )
    if not created:  # Если товар уже в корзине, увеличиваем количество
        cart_item.quantity += 1
        cart_item.save()

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


# Увеличение или уменьшение количества товара в корзине
def update_cart(request, cart_item_id):
    cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
    action = request.POST.get('action')

    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease' and cart_item.quantity > 1:
        cart_item.quantity -= 1

    cart_item.save()
    return redirect('cart')


# Удаление товара из корзины
def delete_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
    cart_item.delete()
    return redirect('cart')


# Оформление заказа
def checkout(request):
    if not request.user.is_authenticated:
        return redirect('login')

    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        return redirect('cart')  # Если корзина пуста, отправляем пользователя назад

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Проверяем данные пользователя в базе данных
            user = User.objects.get(pk=request.user.pk)
            telegram_chat_id = user.telegram_chat_id
            print(f"Telegram ID для пользователя {user.username}: {telegram_chat_id}")

            # Если Telegram ID пустой, выводим предупреждение
            if not telegram_chat_id:
                print(f"Внимание! Telegram ID для пользователя {user.username} отсутствует!")


            # if hasattr(request.user, 'order_set') and request.user.order_set.exists():
            #     telegram_chat_id = request.user.order_set.first().telegram_chat_id
            #     print(f"Найден Telegram ID: {telegram_chat_id} для пользователя: {request.user.username}")
            # else:
            #     print(f"У пользователя {request.user.username} нет Telegram ID.")

            # Создаём заказ
            order = Order.objects.create(
                user=request.user,
                telegram_chat_id=telegram_chat_id,  # Привязываем Telegram ID
                status='accepted',
                total_price=sum(item.product.price * item.quantity for item in cart_items)
            )
            print(
                f"Создан заказ #{order.id} для пользователя {request.user.username} с Telegram ID: {telegram_chat_id}")

            order.products.set(item.product for item in cart_items)  # Связываем товары с заказом
            order.save()

            # Удаляем товары из корзины после оформления заказа
            cart_items.delete()
            # Перенаправляем на страницу подтверждения
            return redirect('order_success')
    else:
        form = OrderForm()

    return render(request, 'main/checkout.html', {'form': form, 'cart_items': cart_items})

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