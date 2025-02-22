import pytest
import warnings
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from main.models import Product, Review, Cart, Order
from main.reports import generate_text_report
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

# ---------------- Фикстуры (подготовка данных для тестов) ----------------

@pytest.fixture
def user(db):
    """Создает тестового пользователя"""
    return User.objects.create_user(username='testuser', password='password123')

@pytest.fixture
def admin_user(db):
    """Создает тестового администратора"""
    user = User.objects.create_user(username='admin', password='admin123', is_staff=True, is_superuser=True)
    return user

@pytest.fixture
def create_image():
    """Создает тестовое изображение"""
    image = BytesIO()
    Image.new("RGB", (100, 100)).save(image, format="JPEG")
    image.seek(0)
    return SimpleUploadedFile("test.jpg", image.getvalue(), content_type="image/jpeg")

@pytest.fixture
def create_product(db, create_image):
    """Создает тестовый товар"""
    return Product.objects.create(name="Тестовый букет", price=1500, image=create_image)

@pytest.fixture
def authenticated_user(client, user):
    """Аутентифицирует пользователя и возвращает его вместе с клиентом"""
    client.force_login(user)
    return user, client

@pytest.fixture
def create_order(db, authenticated_user, create_product):
    """Создает тестовый заказ"""
    user, _ = authenticated_user
    order = Order.objects.create(user=user, total_price=2000, status="delivered", created_at=timezone.now())
    order.products.set([create_product])
    return order

@pytest.fixture
def cart_item(db, user, create_product):
    """Создает элемент корзины"""
    return Cart.objects.create(user=user, product=create_product)

# ---------------- Тесты регистрации и аутентификации ----------------

@pytest.mark.django_db
def test_register_new_user(client):
    """Тест регистрации нового пользователя"""
    response = client.post(reverse('register'), {
        'username': 'testuser',
        'password': 'strongpassword123',
        'password_confirm': 'strongpassword123'
    })
    assert response.status_code == 302
    assert User.objects.count() == 1

@pytest.mark.django_db
def test_invalid_registration(client):
    """Тест неуспешной регистрации при несовпадении паролей"""
    response = client.post(reverse('register'), {
        'username': 'testuser', 'password': 'weakpass', 'password_confirm': 'mismatch'
    })
    assert response.status_code == 200
    assert User.objects.count() == 0

# ---------------- Тесты корзины и заказов ----------------

@pytest.mark.django_db
def test_add_to_cart_authenticated_user(client, authenticated_user, create_product):
    """Тест добавления товара в корзину авторизованным пользователем"""
    user, client = authenticated_user
    response = client.get(reverse('add_to_cart', args=[create_product.id]))
    assert response.status_code == 302
    assert Cart.objects.filter(user=user, product=create_product).exists()

@pytest.mark.django_db
def test_delete_from_cart(client, authenticated_user, cart_item):
    """Тест удаления товара из корзины"""
    user, client = authenticated_user
    url = reverse('remove_from_cart', kwargs={'cart_item_id': cart_item.pk})
    response = client.post(url)
    assert response.status_code == 302
    assert not Cart.objects.filter(pk=cart_item.pk).exists()

# ---------------- Тесты отзывов ----------------

@pytest.mark.django_db
def test_leave_review(client, authenticated_user, create_order):
    """Тест добавления отзыва пользователем"""
    user, client = authenticated_user
    order = create_order
    response = client.post(reverse("leave_review", args=[order.id]), {"text": "Отличный букет!", "rating": 5})
    assert response.status_code == 302
    assert Review.objects.filter(user=user, order=order).exists()

# ---------------- Админские отчёты ----------------

@pytest.mark.django_db
def test_admin_reports(client, admin_user):
    """Тест проверки доступа администратора к отчётам"""
    warnings.simplefilter("ignore", RuntimeWarning)  # Игнорируем предупреждения о временных зонах

    client.force_login(admin_user)
    Order.objects.create(user=admin_user, total_price=1500, status="accepted", created_at=timezone.now())
    response = client.get(reverse("admin_reports"))
    assert response.status_code == 200
    assert "Выручка" in response.content.decode()

@pytest.mark.django_db
def test_generate_text_report(db, admin_user):
    """Тест генерации текстового отчёта"""
    warnings.simplefilter("ignore", RuntimeWarning)  # Игнорируем предупреждения о временных зонах

    Order.objects.create(user=admin_user, total_price=3000, status="accepted", created_at=timezone.now())
    report = generate_text_report()
    assert "Количество заказов" in report
