from main.models import Order, User
from datetime import datetime, timedelta


def generate_text_report():
    """Генерирует подробный текстовый отчет по заказам за все время и за выбранные периоды."""
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Все заказы
    all_orders = Order.objects.all()
    orders_today = all_orders.filter(created_at__date=today)
    orders_week = all_orders.filter(created_at__date__gte=week_ago)
    orders_month = all_orders.filter(created_at__date__gte=month_ago)

    # Подсчеты
    total_orders_all_time = all_orders.count()
    total_orders_today = orders_today.count()
    total_orders_week = orders_week.count()
    total_orders_month = orders_month.count()

    revenue_today = sum(order.total_price for order in orders_today)
    revenue_week = sum(order.total_price for order in orders_week)
    revenue_month = sum(order.total_price for order in orders_month)
    revenue_all_time = sum(order.total_price for order in all_orders)

    average_check = revenue_all_time / total_orders_all_time if total_orders_all_time > 0 else 0

    # Количество заказов по статусам (за все время)
    status_counts = {status: all_orders.filter(status=status).count() for status in ["accepted", "assembling", "on_the_way", "delivered"]}

    # Количество заказов по пользователям (ТОП-5)
    user_orders = {}
    for user in User.objects.filter(order__in=all_orders).distinct():
        user_orders[user.username] = all_orders.filter(user=user).count()
    top_users = sorted(user_orders.items(), key=lambda x: x[1], reverse=True)[:5]  # ТОП-5 пользователей

    # Популярные букеты (ТОП-5)
    bouquet_counts = {}
    for order in all_orders:
        for product in order.products.all():
            bouquet_counts[product.name] = bouquet_counts.get(product.name, 0) + 1
    top_bouquets = sorted(bouquet_counts.items(), key=lambda x: x[1], reverse=True)[:5]  # ТОП-5 букетов

    # Формируем текст отчета
    report_content = (
        f"📅 Отчет за {today.strftime('%d.%m.%Y')}\n\n"
        f"📦 *Количество заказов:*\n"
        f"   - Сегодня: {total_orders_today}\n"
        f"   - За неделю: {total_orders_week}\n"
        f"   - За месяц: {total_orders_month}\n"
        f"   - Всего: {total_orders_all_time}\n\n"
        f"💰 *Выручка:*\n"
        f"   - Сегодня: {revenue_today} руб.\n"
        f"   - За неделю: {revenue_week} руб.\n"
        f"   - За месяц: {revenue_month} руб.\n"
        f"   - Всего: {revenue_all_time} руб.\n\n"
        f"💳 *Средний чек:* {average_check:.2f} руб.\n\n"
        f"📊 *Статистика по статусам (все время):*\n"
        f"   ✅ Принято: {status_counts['accepted']}\n"
        f"   🛠 В сборке: {status_counts['assembling']}\n"
        f"   🚚 В пути: {status_counts['on_the_way']}\n"
        f"   📦 Доставлено: {status_counts['delivered']}\n\n"
        f"👥 *ТОП-5 пользователей по заказам:*\n"
    )

    # Добавляем ТОП-5 пользователей
    if top_users:
        for user, count in top_users:
            report_content += f"   - {user}: {count} заказ(ов)\n"
    else:
        report_content += "   Нет данных.\n"

    # Добавляем ТОП-5 популярных букетов
    report_content += "\n🌸 *ТОП-5 популярных букетов:*\n"
    if top_bouquets:
        for bouquet, count in top_bouquets:
            report_content += f"   - {bouquet}: {count} раз(а)\n"
    else:
        report_content += "   Нет данных.\n"

    return report_content