from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
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
    products = models.ManyToManyField(Product)  # Букеты
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='accepted')  # Статус заказа
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # Общая цена
    created_at = models.DateTimeField(auto_now_add=True)  # Дата оформления
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True)  # Telegram ID пользователя
    address = models.TextField(blank=True)  # Адрес доставки
    card_text = models.TextField(blank=True)  # Текст на открытке
    signature = models.CharField(max_length=255, blank=True)  # Подпись

    def __str__(self):
        return f"Заказ #{self.id} - {self.status}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    # Метод для отслеживания изменения статуса заказа
    def save(self, *args, **kwargs):
        # Проверяем, существует ли заказ, чтобы сравнить старый и новый статус
        if self.pk:
            try:
                old_order = Order.objects.get(pk=self.pk)
            except Order.DoesNotExist:
                old_order = None

            if old_order and old_order.status != self.status:
                # ✅ Откладываем импорт `send_telegram_message`, чтобы избежать циклического импорта
                from telegram_bot import send_telegram_message

                # Формируем сообщение о смене статуса
                message_text = (
                    f"📢 Обновление статуса заказа №{self.id}!\n\n"
                    f"🔄 Новый статус: *{self.get_status_display()}*\n"
                    f"📅 Дата заказа: {self.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"💐 Букет: {self.products.first().name if self.products.exists() else 'Не указан'}\n"
                    f"💰 Цена: {self.total_price} руб.\n\n"
                    "🔔 Ожидайте дальнейшей информации!"
                )

                if self.telegram_chat_id:
                    send_telegram_message(self.telegram_chat_id, message_text)

        super().save(*args, **kwargs)  # Сохранение заказа

    def __str__(self):
        return f"Заказ #{self.id} - {self.user}"


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