from django.contrib import admin
from .models import Product, Order, Review

admin.site.register(Product)
admin.site.register(Review)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'created_at')  # Поля, отображаемые в списке заказов
    list_filter = ('status', 'created_at')  # Фильтрация по статусу и дате
    search_fields = ('user__username',)  # Поиск по имени пользователя
    ordering = ('-created_at',)  # Сортировка по дате создания (от новых к старым)
    list_editable = ('status',)  # Делаем поле "status" редактируемым