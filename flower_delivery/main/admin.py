from django.contrib import admin
from .models import Product, Order, Review
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

admin.site.register(Product)
admin.site.register(Review)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'created_at', 'telegram_chat_id')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username',)
    ordering = ('-created_at',)
    list_editable = ('status',)

# Убираем стандартную регистрацию User
admin.site.unregister(User)

# Настраиваем модель User с твоими настройками
class OrderInline(admin.StackedInline):
    model = Order
    fields = ('telegram_chat_id',)
    readonly_fields = ('telegram_chat_id',)
    extra = 0

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email')
    inlines = [OrderInline]
