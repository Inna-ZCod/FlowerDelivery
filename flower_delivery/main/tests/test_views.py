import pytest
import warnings
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import TestCase, Client
from main.models import Product, Review, Cart, Order
from main.reports import generate_text_report
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone


# ---------------- Регистрация и авторизация -----------------------

# Тестирование регистрации
@pytest.mark.django_db
class RegisterTest(TestCase):

    def test_register_new_user(self):
        response = self.client.post('/register/', {
            'username': 'testuser',
            'password': 'strongpassword123',
            'password_confirm': 'strongpassword123'
        })

        # Проверяем успешную регистрацию
        assert response.status_code == 302  # Код ответа для редиректа
        assert User.objects.count() == 1  # Проверяем создание нового пользователя
        new_user = User.objects.get(username='testuser')
        assert new_user.username == 'testuser'  # Проверяем, что пользователь был создан с правильным именем

    def test_invalid_registration(self):
        response = self.client.post('/register/', {
            'username': 'testuser',
            'password': 'weakpass',
            'password_confirm': 'mismatch'
        })

        # Проверяем неудачную регистрацию
        assert response.status_code == 200  # Ожидаем код ответа 200 (страница с ошибками)
        assert User.objects.count() == 0  # Пользователь не создан


# Тестируем вход пользователя с правильными и неправильными данными:
@pytest.mark.django_db
class LoginTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='testuser',
            password='strongpassword123'
        )

    def test_login_with_correct_credentials(self):
        response = self.client.login(username='testuser', password='strongpassword123')

        # Проверяем успешный вход
        assert response is True
        assert self.client.session['_auth_user_id'] == str(self.user.pk)

    def test_login_with_incorrect_credentials(self):
        response = self.client.login(username='wronguser', password='incorrectpassword')

        # Проверяем неуспешный вход
        assert response is False
        assert '_auth_user_id' not in self.client.session


# Проверим выход пользователя из системы:
@pytest.mark.django_db
class LogoutTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='testuser',
            password='strongpassword123'
        )

    def test_logout_user(self):
        self.client.force_login(self.user)
        response = self.client.get('/logout/')

        # Проверяем успешный выход
        assert response.status_code == 302  # Код ответа для редиректа
        assert '_auth_user_id' not in self.client.session


# Тестирование перенаправления на логин при доступе к защищенным страницам
# Тестируем доступ к странице профиля без входа в систему
@pytest.mark.django_db
class ProfileAccessTest(TestCase):

    def test_redirect_to_login_if_not_logged_in(self):
        response = self.client.get('/profile/')

        # Проверяем редирект на страницу логина
        assert response.status_code == 302
        assert response.url == '/login/'



# ------------------ Работа с каталогом ----------------------

# Тест просмотра каталога
@pytest.mark.django_db
class CatalogViewTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        image_file = BytesIO()
        img = Image.new('RGB', size=(50, 50))
        img.save(image_file, format='JPEG')
        image_file.seek(0)
        for i in range(3):
            Product.objects.create(name=f'Test Product {i}',
                                   price=i * 100,
                                   image=SimpleUploadedFile('test.jpg', image_file.read()))

    def test_catalog_view(self):
        response = self.client.get('/catalog/')

        # Проверяем успешность загрузки страницы
        assert response.status_code == 200

        # Проверяем, что передаются продукты в контексте
        products = response.context['products']
        assert len(products) == 3
        for product in products:
            assert isinstance(product, Product)


# Тест страницы продукта
@pytest.mark.django_db
class ProductDetailViewTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Создаем пользователя
        cls.user = User.objects.create_user(username='testuser', password='password123')

        image_file = BytesIO()
        img = Image.new('RGB', size=(50, 50))
        img.save(image_file, format='JPEG')
        image_file.seek(0)

        cls.product = Product.objects.create(
            name='Test Product',
            price=500,
            image=SimpleUploadedFile('test.jpg', image_file.read())
        )

        for i in range(2):
            Review.objects.create(
                product=cls.product,
                text=f'Test Review {i}',
                rating=i + 1,
                user=cls.user  # Привязываем пользователя к отзыву
            )

    def test_product_detail_view(self):
        response = self.client.get(f'/product/{self.product.id}/')

        # Проверяем успешность загрузки страницы
        assert response.status_code == 200

        # Проверяем, что передан правильный продукт
        product = response.context['product']
        assert product == self.product

        # Проверяем, что переданы отзывы
        reviews = response.context['reviews']
        assert len(reviews) == 2
        for review in reviews:
            assert isinstance(review, Review)



# ----------------------- Оформление заказа -------------------

# Тест на добавление товара в корзину
class AddToCartTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Создаем фиктивное изображение
        img_file = BytesIO()
        image = Image.new('RGB', (100, 100))
        image.save(img_file, format='PNG')
        img_file.seek(0)

        # Создаем объект SimpleUploadedFile
        uploaded_img = SimpleUploadedFile("test_image.png", img_file.read(), content_type='image/png')

        # Создаем пользователя
        cls.user = User.objects.create_user(username='testuser', password='strongpassword123')

        # Создаем продукт с изображением
        cls.product = Product.objects.create(name='Test Product', price=1000, image=uploaded_img)

    def test_add_to_cart_anonymous_user(self):
        """Тестируем перенаправление на страницу логина для анонимного пользователя."""
        response = self.client.get(reverse('add_to_cart', args=[self.product.id]))

        self.assertRedirects(response, '/login/')

    def test_add_to_cart_authenticated_user(self):
        """Тестируем успешное добавление товара в корзину для аутентифицированного пользователя."""
        self.client.login(username='testuser', password='strongpassword123')

        response = self.client.get(reverse('add_to_cart', args=[self.product.id]))

        cart_item = Cart.objects.filter(user=self.user, product=self.product).first()

        self.assertRedirects(response, '/catalog/')  # Проверяем перенаправление на страницу каталога
        self.assertIsNotNone(cart_item)  # Проверяем наличие записи в корзине


# Тест на удаление товара из корзины
@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='password123')


@pytest.fixture
def product():
    return Product.objects.create(name='Test Product', price=500)


@pytest.fixture
def cart_item(user, product):
    return Cart.objects.create(user=user, product=product)


@pytest.mark.django_db
def test_delete_from_cart(client, user, cart_item):
    client.force_login(user)
    url = reverse('remove_from_cart', kwargs={'cart_item_id': cart_item.pk})  # Изменили имя маршрута!
    response = client.post(url)

    assert response.status_code == 302  # Проверяем редирект после успешного удаления
    assert not Cart.objects.filter(pk=cart_item.pk).exists()  # Проверяем отсутствие удаленной записи в корзине



# Тест на подтверждение заказа
@pytest.mark.django_db
def test_confirm_order(client, authenticated_user, create_product):
    """Тест на подтверждение заказа."""
    user, client = authenticated_user
    product = create_product

    cart_item = Cart.objects.create(user=user, product=product)

    response = client.post(reverse("finalize_order"))  # Используем правильный обработчик

    assert response.status_code == 302  # Должен быть редирект
    assert Order.objects.filter(user=user).count() == 1  # Заказ создан
    assert not Cart.objects.filter(user=user).exists()  # Корзина очищена


@pytest.mark.django_db
def test_cart_cleared_after_order(client, authenticated_user, create_product):
    """Тест на очистку корзины после оформления заказа."""
    user, client = authenticated_user
    product = create_product

    Cart.objects.create(user=user, product=product)
    client.post(reverse("finalize_order"))

    assert Cart.objects.filter(user=user).count() == 0  # Корзина должна быть пустой


@pytest.mark.django_db
def test_order_requires_address(client, authenticated_user, create_product):
    """Тест на обязательность поля 'адрес доставки'."""
    user, client = authenticated_user
    product = create_product

    cart_item = Cart.objects.create(user=user, product=product)

    response = client.post(reverse("confirm_order"), {
        f"card_text_{cart_item.id}": "Поздравляю!",
        f"signature_{cart_item.id}": "С любовью",
    })

    assert response.status_code == 302  # Теперь ожидаем редирект
    assert response.url == reverse("cart")  # Проверяем, что редирект ведет в корзину
    assert Order.objects.filter(user=user).count() == 0  # Заказ не должен создаться




# ------------------------ Управление заказами (для администратора) ----------------------

@pytest.mark.django_db
def test_admin_reports(client, authenticated_user):
    """Тест на доступ администратора к отчетам и корректность данных."""
    warnings.simplefilter("ignore", RuntimeWarning)  # Игнорируем предупреждения о временных зонах

    user, client = authenticated_user
    user.is_superuser = True
    user.save()

    Order.objects.create(user=user, total_price=1500, status="accepted", created_at=timezone.now())
    Order.objects.create(user=user, total_price=2000, status="delivered", created_at=timezone.now())

    response = client.get(reverse("admin_reports"))
    assert response.status_code == 200
    assert "Выручка" in response.content.decode()  # Более общее название
    assert "Количество заказов" in response.content.decode()


@pytest.mark.django_db
def test_download_report(client, authenticated_user):
    """Тест на скачивание отчета администратором."""
    warnings.simplefilter("ignore", RuntimeWarning)  # Игнорируем предупреждения

    user, client = authenticated_user
    user.is_staff = True
    user.save()

    response = client.get(reverse("download_report"))
    assert response.status_code == 200
    assert "attachment; filename=order_report.txt" in response["Content-Disposition"]


@pytest.mark.django_db
def test_generate_text_report(db, authenticated_user):
    """Тест генерации текстового отчета."""
    warnings.simplefilter("ignore", RuntimeWarning)  # Игнорируем предупреждения

    user, _ = authenticated_user  # Получаем пользователя
    Order.objects.create(user=user, total_price=3000, status="accepted", created_at=timezone.now())
    report = generate_text_report()

    assert "Количество заказов" in report
    assert "Выручка" in report


# ------------------------------- Отзывы и рейтинги ----------------------------

@pytest.fixture
def create_image():
    """Создает тестовое изображение."""
    image = BytesIO()
    Image.new("RGB", (100, 100)).save(image, format="JPEG")
    image.seek(0)
    return SimpleUploadedFile("test.jpg", image.getvalue(), content_type="image/jpeg")


@pytest.fixture
def create_product(db, create_image):
    """Создает тестовый продукт с изображением."""
    return Product.objects.create(name="Тестовый букет", price=1500, image=create_image)


@pytest.fixture
def create_order(db, authenticated_user, create_product):
    """Создает тестовый заказ с продуктом."""
    user, _ = authenticated_user
    order = Order.objects.create(user=user, total_price=2000, status="delivered", created_at=timezone.now())
    order.products.set([create_product])
    return order


@pytest.mark.django_db
def test_leave_review(client, authenticated_user, create_order):
    """Тест на оставление отзыва пользователем."""
    user, client = authenticated_user
    order = create_order

    response = client.post(reverse("leave_review", args=[order.id]), {"text": "Отличный букет!", "rating": 5})

    assert response.status_code == 302  # Должен быть редирект на страницу продукта
    assert Review.objects.filter(user=user, order=order).exists()  # Отзыв должен сохраниться


@pytest.mark.django_db
def test_cannot_leave_duplicate_review(client, authenticated_user, create_order):
    """Тест: пользователь не может оставить повторный отзыв на один заказ."""
    user, client = authenticated_user
    order = create_order
    Review.objects.create(user=user, product=order.products.first(), order=order, text="Хорошо", rating=4)

    response = client.post(reverse("leave_review", args=[order.id]), {"text": "Плохой букет", "rating": 1})

    assert response.status_code == 302  # Должен быть редирект, но отзыв не должен измениться
    review = Review.objects.get(user=user, order=order)
    assert review.text == "Хорошо"  # Отзыв остался прежним
    assert review.rating == 4  # Рейтинг не изменился


@pytest.mark.django_db
def test_reviews_displayed_on_product_page(client, authenticated_user, create_product):
    """Тест на отображение отзывов на странице продукта."""
    user, client = authenticated_user
    product = create_product
    Review.objects.create(user=user, product=product, text="Лучший букет!", rating=5, created_at=timezone.now())

    response = client.get(reverse("product_detail", args=[product.id]))

    assert response.status_code == 200
    assert "Лучший букет!" in response.content.decode()  # Проверяем, что отзыв отображается



#     Тесты для Telegram-бота
#     Проверим:
#         Обработку команд /start, /connect, /admin_panel.
#         Реакцию на нажатие кнопок, например "Мои заказы".
