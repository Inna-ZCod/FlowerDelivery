import os
import django
import pytest
from main.models import Product
from django.contrib.auth.models import User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings')  
django.setup()

@pytest.fixture
def create_product(db):
    """Создает тестовый продукт"""
    return Product.objects.create(name="Тестовый букет", price=1500)

@pytest.fixture
def authenticated_user(client):
    """Создает пользователя и аутентифицирует его"""
    user = User.objects.create_user(username='testuser', password='password123')
    client.login(username='testuser', password='password123')  # Вход в систему
    return user, client