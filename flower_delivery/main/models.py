from django.db import models
from django.contrib.auth.models import User


# Модель товара (букета)
class Product(models.Model):
    name = models.CharField(max_length=255)  # Название букета
    description = models.TextField(blank=True)  # Описание
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена
    image = models.ImageField(upload_to='products/')  # Изображение букета

    def __str__(self):
        return self.name


# Модель заказа
class Order(models.Model):
    STATUS_CHOICES = [
        ('accepted', 'Принят'),
        ('assembling', 'В сборке'),
        ('on_the_way', 'В пути'),
        ('delivered', 'Доставлен'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Пользователь
    products = models.ManyToManyField(Product)  # Букеты
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='accepted')  # Статус заказа
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # Общая цена
    created_at = models.DateTimeField(auto_now_add=True)  # Дата оформления

    def __str__(self):
        return f"Заказ #{self.id} - {self.status}"


# Модель отзыва
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Пользователь
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Товар
    text = models.TextField()  # Текст отзыва
    rating = models.PositiveIntegerField()  # Рейтинг (1-5)
    created_at = models.DateTimeField(auto_now_add=True)  # Дата отзыва

    def __str__(self):
        return f"Отзыв от {self.user.username} - {self.rating} звезды"


# модель для хранения информации о корзине
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Пользователь, владелец корзины
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Товар в корзине
    quantity = models.PositiveIntegerField(default=1)  # Количество одного и того же товара

    def __str__(self):
        return f"{self.product.name} x {self.quantity} (в корзине {self.user.username})"