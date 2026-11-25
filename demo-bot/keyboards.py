from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import SERVICES

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton(text="📅 Записаться на услугу", callback_data="start_booking")],
        [InlineKeyboardButton(text="📋 Каталог услуг и цены", callback_data="catalog")],
        [InlineKeyboardButton(text="📍 Контакты и время работы", callback_data="contacts")],
        [InlineKeyboardButton(text="❓ Задать вопрос менеджеру", callback_data="ask_question")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_services_keyboard():
    keyboard = []
    for srv_id, srv_data in SERVICES.items():
        text = f"{srv_data['name']} — {srv_data['price']} ₽"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"book_{srv_id}")])
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_dates_keyboard():
    # Демо-даты: Сегодня, Завтра, Послезавтра
    keyboard = [
        [InlineKeyboardButton(text="Сегодня (15:00 - 18:00)", callback_data="date_Сегодня (15:00)")],
        [InlineKeyboardButton(text="Завтра (11:00 - 14:00)", callback_data="date_Завтра (11:00)")],
        [InlineKeyboardButton(text="Завтра (16:00 - 19:00)", callback_data="date_Завтра (16:00)")],
        [InlineKeyboardButton(text="Выбрать другое время вручную", callback_data="date_custom")],
        [InlineKeyboardButton(text="⬅️ Отмена", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_phone_request_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)],
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
