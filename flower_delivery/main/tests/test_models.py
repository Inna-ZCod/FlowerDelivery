import pytest
from main.models import User, Order, Product, Review, Cart


# Тест для модели User
# Проверяем корректность строкового представления (__str__)
# Проверяем поле telegram_chat_id
@pytest.mark.django_db
def test_user_model():
    # Проверяем создание пользователя
    user = User.objects.create(username="testuser")
    assert str(user) == "testuser"  # Проверяем строковое представление
    assert user.telegram_chat_id is None  # Проверяем, что Telegram ID по умолчанию None


# Тест модели Product
# Убедимся, что все поля (name, description, price, image) сохраняются корректно
# Убеждаемся, что строковое представление модели — это название букета (name)
# Проверяем, что можно обновить данные, например, цену (price) или изображение (image)
# Проверяем, что поле description может быть пустым (потому что оно blank=True)
@pytest.mark.django_db
def test_product_model():
    # Создаем объект товара
    product = Product.objects.create(
        name="Букет Тюльпанов",
        description="Нежный букет из 25 розовых тюльпанов",
        price=2500.00,
        image="products/tulips.jpg"
    )

    # Проверяем правильность сохранения данных
    assert product.name == "Букет Тюльпанов"
    assert product.description == "Нежный букет из 25 розовых тюльпанов"
    assert product.price == 2500.00
    assert product.image.name == "products/tulips.jpg"

    # Проверяем строковое представление объекта
    assert str(product) == "Букет Тюльпанов"

    # Проверяем обновление данных
    product.price = 3000.00
    product.save()
    assert product.price == 3000.00

    # Проверяем, что описание может быть пустым
    product.description = ""
    product.save()
    assert product.description == ""

    # Проверяем, что изображение сохраняется корректно
    product.image = "products/new_image.jpg"
    product.save()
    assert product.image.name == "products/new_image.jpg"


# Тест для модели Order
# Проверяем, что все поля (user, status, total_price, telegram_chat_id, address, card_text, signature) сохраняются правильно
# Проверяем, что продукты корректно добавляются к заказу и привязываются через ManyToManyField
# Убеждаемся, что строка формируется как "Заказ #<id> - testuser"
# Проверяем, что статусы заказа могут изменяться последовательно: "accepted" -> "assembling" -> "on_the_way" -> "delivered"
@pytest.mark.django_db
def test_order_model():
    # Создаем тестовые данные
    user = User.objects.create(username="testuser")
    product1 = Product.objects.create(name="Букет Роз", price=1500)
    product2 = Product.objects.create(name="Букет Лилий", price=2000)

    # Создаем объект заказа
    order = Order.objects.create(
        user=user,
        status="accepted",
        total_price=3500,
        telegram_chat_id="123456789",
        address="г. Москва, ул. Пушкина, д. Колотушкина",
        card_text="С любовью",
        signature="Ваш друг"
    )

    # Привязываем продукты к заказу
    order.products.set([product1, product2])

    # Проверяем правильность хранения данных
    assert order.user == user
    assert order.status == "accepted"
    assert order.total_price == 3500
    assert order.telegram_chat_id == "123456789"
    assert order.address == "г. Москва, ул. Пушкина, д. Колотушкина"
    assert order.card_text == "С любовью"
    assert order.signature == "Ваш друг"

    # Проверяем связанные продукты
    assert list(order.products.all()) == [product1, product2]

    # Проверяем строковое представление объекта
    assert str(order) == f"Заказ #{order.id} - {user}"

    # Проверяем статусы заказа
    order.status = "assembling"
    order.save()
    assert order.status == "assembling"

    order.status = "on_the_way"
    order.save()
    assert order.status == "on_the_way"

    order.status = "delivered"
    order.save()
    assert order.status == "delivered"


# Тест для модели Review
# Проверяем, что все поля сохраняются правильно (user, product, order, text, rating)
# Убеждаемся, что строка формируется как "Отзыв от testuser - 5 ⭐"
# Пробуем создать еще один отзыв с теми же user и order. Ожидаем, что это вызовет исключение, так как повторные отзывы запрещены
@pytest.mark.django_db
def test_review_model():
    # Создаем тестовые данные
    user = User.objects.create(username="testuser")
    product = Product.objects.create(name="Тестовый продукт", price=100)
    order = Order.objects.create(user=user, total_price=100, status="accepted")

    # Создаем объект отзыва
    review = Review.objects.create(
        user=user,
        product=product,
        order=order,
        text="Отличный букет! Очень понравился.",
        rating=5
    )

    # Проверяем правильность хранения данных
    assert review.user == user
    assert review.product == product
    assert review.order == order
    assert review.text == "Отличный букет! Очень понравился."
    assert review.rating == 5

    # Проверяем строковое представление объекта
    assert str(review) == f"Отзыв от {user.username} - {review.rating} ⭐"

    # Проверяем уникальность отзыва для одной пары user-order
    with pytest.raises(Exception):
        Review.objects.create(
            user=user,
            product=product,
            order=order,
            text="Еще один отзыв",
            rating=4
        )


# Тест модели Cart
# Проверка для полей address, card_text и signature
# Корректность строкового представления (__str__)
@pytest.mark.django_db
def test_cart_model():
    # Создаем тестовые данные
    user = User.objects.create(username="testuser")
    product = Product.objects.create(name="Тестовый продукт", price=100)

    # Создаем объект корзины
    cart_item = Cart.objects.create(
        user=user,
        product=product,
        address="Тестовый адрес",
        card_text="Поздравляю с днем рождения!",
        signature="С любовью, Тест"
    )

    # Проверяем правильность хранения данных
    assert cart_item.user == user
    assert cart_item.product == product
    assert cart_item.address == "Тестовый адрес"
    assert cart_item.card_text == "Поздравляю с днем рождения!"
    assert cart_item.signature == "С любовью, Тест"

    # Проверяем строковое представление объекта
    assert str(cart_item) == f"{product.name} для {user.username}"
