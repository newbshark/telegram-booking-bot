import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv

load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID", "657055853"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://vadim-tutor.web.app")

def get_main_keyboard(user_id: int = 0):
    kb = [
        [InlineKeyboardButton(text="🚀 Открыть интерактивную Web-студию", web_app=WebAppInfo(url=WEBAPP_URL))],
        [
            InlineKeyboardButton(text="🎯 Пройти тест (40 сек)", callback_data="start_quiz"),
            InlineKeyboardButton(text="🎁 Пробный урок (0 ₽)", callback_data="book_trial")
        ],
        [
            InlineKeyboardButton(text="🎮 Каталог направлений", callback_data="show_courses"),
            InlineKeyboardButton(text="💰 Тарифы и абонементы", callback_data="show_prices")
        ],
        [
            InlineKeyboardButton(text="❓ Частые вопросы (FAQ)", callback_data="show_faq"),
            InlineKeyboardButton(text="👨‍💻 О наставнике (Вадим)", callback_data="about_me")
        ],
        [
            InlineKeyboardButton(text="💬 Написать в Telegram", url="https://t.me/mrvasilievv"),
            InlineKeyboardButton(text="✍️ Задать вопрос в боте", callback_data="ask_in_bot")
        ],
        [InlineKeyboardButton(text="🤝 Партнерская программа (+2 000 ₽)", callback_data="partner_program")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_courses_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕹️ Unity 3D — Создание игр с нуля", callback_data="course_unity")],
        [InlineKeyboardButton(text="🏎️ GTA 5 Моддинг на C#", callback_data="course_gta")],
        [InlineKeyboardButton(text="📚 Школьный индивидуальный проект (ИИП)", callback_data="course_project")],
        [InlineKeyboardButton(text="🌐 Создание сайтов (Frontend с нуля)", callback_data="course_web")],
        [InlineKeyboardButton(text="⚡ Arduino и Схемотехника", callback_data="course_arduino")],
        [InlineKeyboardButton(text="✨ Открыть витрину в Web App", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])

def get_faq_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💻 Нужен ли мощный компьютер?", callback_data="faq_pc")],
        [InlineKeyboardButton(text="🌐 Как проходят занятия онлайн?", callback_data="faq_format")],
        [InlineKeyboardButton(text="👶 С какого возраста берете ребят?", callback_data="faq_age")],
        [InlineKeyboardButton(text="⏰ Сколько длится урок и расписание?", callback_data="faq_timing")],
        [InlineKeyboardButton(text="✍️ Задать свой вопрос наставнику", callback_data="ask_in_bot")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])

def get_prices_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Записаться на бесплатный пробный урок", callback_data="book_trial")],
        [InlineKeyboardButton(text="✨ Рассчитать тариф в Web App", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])

def get_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Свежие заявки (NEW)", callback_data="admin_leads_new")],
        [InlineKeyboardButton(text="📋 Все заявки", callback_data="admin_leads_all")],
        [InlineKeyboardButton(text="📊 Аналитика и цифры", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Сделать рассылку по базе", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="◀️ Выйти в главное меню", callback_data="back_to_menu")]
    ])

def get_lead_actions_keyboard(lead_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📞 Связался", callback_data=f"lead_status_{lead_id}_CONTACTED"),
            InlineKeyboardButton(text="📅 Пробный назначен", callback_data=f"lead_status_{lead_id}_SCHEDULED")
        ],
        [
            InlineKeyboardButton(text="💰 Оплатил абонемент", callback_data=f"lead_status_{lead_id}_PAID"),
            InlineKeyboardButton(text="❌ Архив/Отказ", callback_data=f"lead_status_{lead_id}_ARCHIVE")
        ],
        [InlineKeyboardButton(text="◀️ Назад к заявкам", callback_data="admin_leads_all")]
    ])

def get_partner_keyboard(bot_username: str, user_id: int):
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Скопировать реферальную ссылку", url=ref_link)],
        [InlineKeyboardButton(text="💬 Написать Вадиму по сотрудничеству", url="https://t.me/mrvasilievv")],
        [InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data="back_to_menu")]
    ])
