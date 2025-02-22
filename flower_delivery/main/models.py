from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator



# Расширяем стандартную модель User
User.add_to_class('telegram_chat_id', models.CharField(max_length=50, blank=True, null=True))


# Модель товара (букета)
class Product(models.Model):
    name = models.CharField(max_length=255)  # Название букета
    description = models.TextField(blank=True)  # Описание
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена
    image = models.ImageField(upload_to='products/')  # Изображение букета

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Товар"  # Название модели в единственном числе
        verbose_name_plural = "Товары"  # Название модели во множественном числе


# Модель заказа
class Order(models.Model):
    STATUS_CHOICES = [
        ('accepted', 'Принят'),
        ('assembling', 'В сборке'),
        ('on_the_way', 'В пути'),
        ('delivered', 'Доставлен'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Пользователь
    products = models.ManyToManyField(Product)  # Связь с букетами
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='accepted')  # Статус заказа
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # Общая цена
    created_at = models.DateTimeField(auto_now_add=True)  # Дата оформления заказа
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True)  # Telegram ID пользователя
    address = models.TextField(blank=True)  # Адрес доставки
    card_text = models.TextField(blank=True)  # Текст на открытке
    signature = models.CharField(max_length=255, blank=True)  # Подпись

    def __str__(self):
        return f"Заказ #{self.id} - {self.user}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


# Модель отзыва
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Пользователь
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Товар
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="review", blank=True)  # Связь с заказом (1 отзыв на 1 заказ)
    text = models.TextField(blank=True, null=True)  # Текст отзыва (необязательный)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )  # Рейтинг от 1 до 5
    created_at = models.DateTimeField(auto_now_add=True)  # Дата отзыва

    def __str__(self):
        return f"Отзыв от {self.user.username} - {self.rating} ⭐"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        unique_together = ('user', 'order')  # Запрещаем повторные отзывы к одному заказу


# модель для хранения информации о корзине
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Пользователь, владелец корзины
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Товар в корзине
    address = models.TextField(blank=True, default="")  # Адрес доставки
    card_text = models.TextField(blank=True, default="")  # Текст на открытке
    signature = models.CharField(max_length=255, blank=True, default="")  # Подпись

    def __str__(self):
        return f"{self.product.name} для {self.user.username}"