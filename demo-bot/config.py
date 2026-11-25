# Конфигурация демонстрационного бота
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "bookings.db")

# Услуги и цены по умолчанию
SERVICES = {
    "srv_1": {"name": "Экспресс-диагностика / Консультация", "price": 1500, "duration": "30 мин"},
    "srv_2": {"name": "Комплексная настройка / Услуга", "price": 4500, "duration": "1.5 часа"},
    "srv_3": {"name": "Премиум обслуживание 'Под ключ'", "price": 9900, "duration": "3 часа"},
}
