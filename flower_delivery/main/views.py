from django.shortcuts import render, get_object_or_404, redirect
from .forms import OrderForm
from .models import Product, Cart, Order


def home(request):
    return render(request, 'main/home.html')

def catalog(request):
    products = Product.objects.all()
    return render(request, 'main/catalog.html', {'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)  # Получаем товар по ID или возвращаем 404
    return render(request, 'main/product_detail.html', {'product': product})


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

    return redirect('cart')  # Перенаправляем пользователя в корзину


# Отображение корзины
def cart(request):
    if not request.user.is_authenticated:
        return redirect('login')

    cart_items = Cart.objects.filter(user=request.user)  # Получаем товары в корзине
    for item in cart_items:
        item.total_price = item.product.price * item.quantity  # Вычисляем "Итого" для каждого товара
    total_price = sum(item.product.price * item.quantity for item in cart_items)  # Общая стоимость
    return render(request, 'main/cart.html', {'cart_items': cart_items, 'total_price': total_price})


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
            # Создаём заказ
            order = Order.objects.create(
                user=request.user,
                status='accepted',
                total_price=sum(item.product.price * item.quantity for item in cart_items)
            )
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