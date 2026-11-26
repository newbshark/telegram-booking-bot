#!/usr/bin/env python3
import asyncio
import logging
import html
import json
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import database as db
import keyboards as kb

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Initialize DB on import
db.init_db()

# --- FSM STATES ---
class QuizStates(StatesGroup):
    q1_age = State()
    q2_games = State()
    q3_exp = State()
    q4_goal = State()
    get_contact = State()

class BroadcastStates(StatesGroup):
    waiting_for_message = State()

class ClientQuestionStates(StatesGroup):
    waiting_for_question = State()

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://vadim-tutor.web.app")

# --- /APP COMMAND ---
@dp.message(Command("app"))
async def cmd_app(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Запустить интерактивную студию", web_app=types.WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_to_menu")]
    ])
    await message.answer(
        "╭───────────────────────────────╮\n"
        "│  ✨ <b>ИНТЕРАКТИВНАЯ WEB-СТУДИЯ ВАДИМА</b>\n"
        "╰───────────────────────────────╯\n\n"
        "Полноэкранное приложение прямо внутри Telegram:\n"
        "• 🎯 <b>Экспресс-квиз</b> по подбору направления\n"
        "• 🎮 <b>Витрина программ</b> с подробным описанием\n"
        "• 💰 <b>Калькулятор тарифов</b> и абонементов\n"
        "• 🎁 <b>1-клик бронирование</b> бесплатного пробного урока\n\n"
        "Нажмите кнопку ниже для запуска:",
        reply_markup=markup,
        parse_mode="HTML"
    )

# --- /START COMMAND ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    # Check referral code (e.g. /start ref_12345)
    referrer_id = None
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            ref_str = args[1].replace("ref_", "")
            if ref_str.isdigit():
                referrer_id = int(ref_str)
                if referrer_id == message.from_user.id:
                    referrer_id = None
        except Exception:
            pass

    # Save user to DB
    db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        referrer_id=referrer_id
    )

    user_name = message.from_user.first_name or "друг"
    text = (
        f"╭───────────────────────────────╮\n"
        f"│  ⚡ <b>VADIM // GAME DEV & IT MENTOR</b>\n"
        f"│  <i>Персональная IT-лаборатория для подростков</i>\n"
        f"╰───────────────────────────────╯\n\n"
        f"👋 Здравствуйте, <b>{html.escape(user_name)}</b>!\n\n"
        "Я <b>Вадим</b> — действующий программист и частный наставник по разработке игр и IT для ребят (8–16 лет).\n\n"
        "🎮 <b>Наш принцип:</b> обучение через живой интерес ребенка. Мы не зубрим оторванную от жизни теорию, а сразу создаем <b>3D-игры в Unity</b> и пишем настоящий рабочий код на <b>C#</b> с первого урока.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨ <b>ВЫБЕРИТЕ ДЕЙСТВИЕ ИЛИ ОТКРОЙТЕ СТУДИЮ:</b>"
    )
    await message.answer(text, reply_markup=kb.get_main_keyboard(message.from_user.id), parse_mode="HTML")

# --- BACK TO MENU ---
@dp.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Выберите интересующий раздел или запишитесь на бесплатный пробный урок:",
        reply_markup=kb.get_main_keyboard(callback.from_user.id)
    )

# --- ABOUT ME ---
@dp.callback_query(F.data == "about_me")
async def cb_about_me(callback: types.CallbackQuery):
    text = (
        "╭───────────────────────────────╮\n"
        "│  👨‍💻 <b>О НАСТАВНИКЕ // ВАДИМ ВАСИЛЬЕВ</b>\n"
        "╰───────────────────────────────╯\n\n"
        "Меня зовут <b>Вадим</b>. Я практикующий разработчик с 4+ годами коммерческого опыта в IT и персональный наставник.\n\n"
        "<b>В чем ключевые отличия от обычных онлайн-школ:</b>\n\n"
        "💎 <b>1. Строго индивидуально 1 на 1:</b>\n"
        "Никаких групп по 12 человек. Преподаватель не меняется от урока к уроку, мы работаем в комфортном темпе ребенка.\n\n"
        "🕹️ <b>2. Обучение на понятных играх:</b>\n"
        "Логику, условия, циклы и ООП мы изучаем на реальных движках (Unity 3D, C# в GTA 5), а не на оторванных от жизни задачках.\n\n"
        "📊 <b>3. Прозрачность для родителей:</b>\n"
        "После каждого занятия вы получаете отчет — что именно ребенок написал своими руками и какой проект собрал.\n\n"
        "⚡ <b>4. Интерактивная среда:</b>\n"
        "Используем визуализаторы памяти (RAM), симуляторы электроники и боевые арены.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 <b>Бесплатный первый урок (40 минут):</b> познакомимся, протестируем интерес и напишем первый рабочий скрипт!\n\n"
        "💬 <b>Прямая связь со мной в Telegram:</b> @mrvasilievv"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Записаться на пробный урок", callback_data="book_trial")],
        [
            InlineKeyboardButton(text="💬 В Telegram", url="https://t.me/mrvasilievv"),
            InlineKeyboardButton(text="✍️ Задать вопрос в боте", callback_data="ask_in_bot")
        ],
        [InlineKeyboardButton(text="✨ Открыть витрину в Web App", web_app=types.WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

# --- ASK QUESTION IN BOT ---
@dp.callback_query(F.data == "ask_in_bot")
async def cb_ask_in_bot(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ClientQuestionStates.waiting_for_question)
    text = (
        "✍️ <b>Задать вопрос наставнику:</b>\n\n"
        "Напишите ваш вопрос прямо в ответном сообщении (например: возраст ребенка, удобные дни, технические требования к ПК).\n\n"
        "Вадим мгновенно получит ваше сообщение и ответит вам.\n\n"
        "<i>Для отмены нажмите кнопку ниже:</i>"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

@dp.message(ClientQuestionStates.waiting_for_question)
async def msg_client_question(message: types.Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    user_handle = f"@{user.username}" if user.username else f"ID: {user.id}"
    user_name = user.full_name or "Родитель"

    admin_alert = (
        f"📩 <b>НОВЫЙ ВОПРОС ОТ КЛИЕНТА В БОТЕ!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>От кого:</b> {html.escape(user_name)} ({user_handle})\n"
        f"💬 <b>Текст вопроса:</b>\n"
        f"<i>{html.escape(message.text)}</i>\n\n"
        f"👉 Чтобы ответить, напишите: {user_handle}"
    )

    markup = None
    if user.username:
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"💬 Ответить {user.first_name}", url=f"https://t.me/{user.username}")]
        ])

    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_alert, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error forwarding client question to admin: {e}")

    await message.answer(
        "✅ <b>Ваш вопрос успешно передан Вадиму!</b>\n\n"
        "Наставник ответит вам в Telegram в ближайшее время.",
        reply_markup=kb.get_main_keyboard(user.id),
        parse_mode="HTML"
    )

# --- PRICES & ABONEMENTS ---
@dp.callback_query(F.data == "show_prices")
async def cb_show_prices(callback: types.CallbackQuery):
    text = (
        "╭───────────────────────────────╮\n"
        "│  💰 <b>ТАРИФЫ И ФОРМАТ АБОНЕМЕНТОВ</b>\n"
        "╰───────────────────────────────╯\n\n"
        "Все занятия проходят строго индивидуально (90 минут) онлайн (Discord / Zoom / Telegram).\n\n"
        "• 🎁 <b>Пробный урок-диагностика (40 минут):</b> <b>0 ₽ (БЕСПЛАТНО)</b>\n"
        "<i>Знакомимся с ребенком, пишем первый скрипт, определяем сильные стороны.</i>\n\n"
        "• 🎟 <b>Разовое занятие (90 минут):</b> <b>2 000 ₽</b>\n"
        "<i>Индивидуальный урок без фиксации слота в постоянном графике.</i>\n\n"
        "• ⭐ <b>Абонемент на 8 занятий (1 месяц, 2 раза в неделю):</b> <b>12 000 ₽</b>\n"
        "<i>(Всего 1 500 ₽ за 90 мин вместо 2 000 ₽. Скидка 4 000 ₽, фиксация удобного слота в расписании, отчеты родителю после каждого урока + проверка домашних проектов).</i>\n\n"
        "• 📦 <b>Курс «Школьный проект под ключ» (4–6 занятий):</b> <b>от 7 500 ₽</b>\n"
        "<i>Разработка рабочей игры/сайта/бота + паспорт проекта + подготовка к защите на «5».</i>"
    )
    await callback.message.edit_text(text, reply_markup=kb.get_prices_keyboard(), parse_mode="HTML")

# --- COURSES CATALOG ---
@dp.callback_query(F.data == "show_courses")
async def cb_show_courses(callback: types.CallbackQuery):
    text = "🎮 <b>Выберите программу обучения, чтобы узнать подробности:</b>"
    await callback.message.edit_text(text, reply_markup=kb.get_courses_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "course_gta")
async def cb_course_gta(callback: types.CallbackQuery):
    text = (
        "🏎️ <b>GTA 5 Моддинг на C# (для подростков 11–16 лет):</b>\n\n"
        "Хит среди ребят. Вместо унылых блок-схем мы открываем код на языке C# и модифицируем поведение игры.\n\n"
        "<b>Чему научится ребенок:</b>\n"
        "• Синтаксис языка C#: переменные, функции, условные операторы, циклы.\n"
        "• Создание скриптов: спавн машин, кастомная физика, телепорты, эффекты, реакция NPC.\n"
        "• Понимание работы памяти компьютера (RAM) и игровых циклов.\n"
        "• В конце трека — ребенок собирает собственный готовый мод-пак."
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Записаться на пробный урок", callback_data="book_trial")],
        [InlineKeyboardButton(text="◀️ Назад к курсам", callback_data="show_courses")]
    ])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

@dp.callback_query(F.data == "course_unity")
async def cb_course_unity(callback: types.CallbackQuery):
    text = (
        "🕹️ <b>Unity 3D — Разработка 3D-игр с нуля (10–16 лет):</b>\n\n"
        "Профессиональный игровой движок Unity, на котором создаются тысячи мобильных и ПК-игр.\n\n"
        "<b>Чему научится ребенок:</b>\n"
        "• Работа в 3D-пространстве (координаты X, Y, Z, освещение, камеры).\n"
        "• Физика Rigidbody: гравитация, столкновения, прыжки, стрельба.\n"
        "• Написание скриптов игровой логики на C#.\n"
        "• Сборка и экспорт игры в готовый самостоятельный файл (.exe), который запускается на любом ПК без Unity."
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Записаться на пробный урок", callback_data="book_trial")],
        [InlineKeyboardButton(text="◀️ Назад к курсам", callback_data="show_courses")]
    ])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

@dp.callback_query(F.data == "course_project")
async def cb_course_project(callback: types.CallbackQuery):
    text = (
        "📚 <b>Школьный индивидуальный проект по информатике (ИИП 8–11 класс):</b>\n\n"
        "Обязательный проект для аттестата. Помогаем школьнику разработать реальный IT-продукт и блестяще защитить его перед комиссией.\n\n"
        "<b>Что входит в подготовку:</b>\n"
        "• Выбор актуальной темы и создание рабочего IT-продукта (игра в Unity, сайт, Telegram-бот или устройство на Arduino).\n"
        "• Оформление паспорта проекта и пояснительной записки по ГОСТу.\n"
        "• Создание презентации и репетиция защиты перед комиссией.\n"
        "• Срок подготовки: всего 4–6 занятий."
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Записаться на пробный урок", callback_data="book_trial")],
        [InlineKeyboardButton(text="◀️ Назад к курсам", callback_data="show_courses")]
    ])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

@dp.callback_query(F.data == "course_web")
async def cb_course_web(callback: types.CallbackQuery):
    text = (
        "🌐 <b>Создание сайтов и веб-разработка (Frontend с нуля):</b>\n\n"
        "Практический курс создания современных веб-страниц.\n\n"
        "<b>Чему научится ребенок:</b>\n"
        "• Верстка на HTML5 и современный CSS (стили, адаптивность под смартфоны, анимации).\n"
        "• Интерактивная логика на JavaScript: кнопки, квизы, калькуляторы, формы заявок.\n"
        "• Публикация своего первого сайта в интернете."
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Записаться на пробный урок", callback_data="book_trial")],
        [InlineKeyboardButton(text="◀️ Назад к курсам", callback_data="show_courses")]
    ])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

@dp.callback_query(F.data == "course_arduino")
async def cb_course_arduino(callback: types.CallbackQuery):
    text = (
        "⚡ <b>Робототехника и Схемотехника на Arduino:</b>\n\n"
        "Курс для юных инженеров (от умного светофора до парктроников и сервоприводов).\n\n"
        "<b>Программа:</b>\n"
        "• Схемотехника: резисторы, потенциометры, светодиоды, датчики расстояния.\n"
        "• Программирование микроконтроллеров на C++ / Wiring.\n"
        "• Симуляция в Tinkercad + сборка на реальных платах."
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Записаться на пробный урок", callback_data="book_trial")],
        [InlineKeyboardButton(text="◀️ Назад к курсам", callback_data="show_courses")]
    ])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

# --- FAQ ---
@dp.callback_query(F.data == "show_faq")
async def cb_show_faq(callback: types.CallbackQuery):
    text = "❓ <b>Часто задаваемые вопросы родителей:</b>\nВыберите тему:"
    await callback.message.edit_text(text, reply_markup=kb.get_faq_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "faq_pc")
async def cb_faq_pc(callback: types.CallbackQuery):
    text = (
        "💻 <b>Нужен ли мощный игровой компьютер?</b>\n\n"
        "Для старта достаточно любого обычного рабочего ноутбука или ПК на Windows или Mac (от 4–8 ГБ оперативной памяти).\n"
        "Все учебные движки и программы (Visual Studio Code, Unity базовые сцены, симуляторы) оптимизированы и не требуют дорогого железа."
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад к FAQ", callback_data="show_faq")]])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

@dp.callback_query(F.data == "faq_format")
async def cb_faq_format(callback: types.CallbackQuery):
    text = (
        "🌐 <b>Как проходят онлайн-занятия?</b>\n\n"
        "Урок проходит в Discord, Zoom или Telegram с демонстрацией экрана. Ребенок сам пишет код на своем компьютере, а я направляю, подсказываю и помогаю исправить ошибки в режиме реального времени.\n\n"
        "После урока ученику остается конспект и памятка, а родителю отправляется отчет о проделанной работе."
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад к FAQ", callback_data="show_faq")]])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

@dp.callback_query(F.data == "faq_age")
async def cb_faq_age(callback: types.CallbackQuery):
    text = (
        "👶 <b>С какого возраста можно начинать?</b>\n\n"
        "Оптимальный возраст — <b>от 9 до 16 лет</b>.\n"
        "• Для ребят 9–11 лет отлично заходит визуальный геймдев и основы сайтов.\n"
        "• Для 11–16 лет — полноценный C#, Unity 3D, моддинг в GTA 5 и школьные индивидуальные проекты."
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад к FAQ", callback_data="show_faq")]])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

@dp.callback_query(F.data == "faq_timing")
async def cb_faq_timing(callback: types.CallbackQuery):
    text = (
        "⏰ <b>Сколько длится урок и какое расписание?</b>\n\n"
        "Стандартное занятие длится <b>90 минут</b> (1.5 часа) — этого времени идеально хватает, чтобы разобрать новую механику и получить законченный работающий скрипт.\n\n"
        "Занятия обычно проходят 1 или 2 раза в неделю в удобные для вас дни (будни вечер или выходные). Расписание фиксируется индивидуально."
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад к FAQ", callback_data="show_faq")]])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

# --- PARTNER PROGRAM ---
@dp.callback_query(F.data == "partner_program")
async def cb_partner(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    name = callback.from_user.full_name or "Коллега"
    partner = db.get_or_create_partner(user_id, name, callback.from_user.username or "")
    
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    text = (
        "🤝 <b>Партнерская программа для репетиторов и учителей:</b>\n\n"
        "Если вы преподаете математику, физику, английский язык или ведете школьные курсы — вы можете получать <b>2 000 ₽ с каждого приведенного ученика</b>!\n\n"
        "<b>Как это устроено:</b>\n"
        "1. Вы делитесь своей персональной ссылкой с родителями учеников, которым интересно программирование или создание игр.\n"
        "2. Родитель переходит в бота, записывается на бесплатный пробный урок.\n"
        "3. Когда родитель оплачивает свой первый абонемент (8 уроков) — вам мгновенно начисляется <b>2 000 ₽</b> (выплата на любую карту РФ).\n\n"
        f"📊 <b>Ваша статистика:</b>\n"
        f"• Перешло по вашей ссылке: <b>{partner['leads_count']}</b>\n"
        f"• Заработано бонусов: <b>{partner['balance']} ₽</b>\n\n"
        f"🔗 <b>Ваша персональная партнерская ссылка:</b>\n"
        f"<code>{ref_link}</code>\n<i>(Нажмите на ссылку, чтобы скопировать)</i>"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать Вадиму напрямую", url="https://t.me/mrvasilievv")],
        [InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

# --- QUIZ HANDLERS ---
@dp.callback_query(F.data == "start_quiz")
async def cb_start_quiz(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(QuizStates.q1_age)
    kb_q = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👶 8–10 лет", callback_data="age_8_10")],
        [InlineKeyboardButton(text="👦 11–13 лет", callback_data="age_11_13")],
        [InlineKeyboardButton(text="🧑 14–16+ лет", callback_data="age_14_16")]
    ])
    await callback.message.edit_text(
        "<b>Вопрос 1 из 4:</b> Сколько лет вашему ребенку?",
        reply_markup=kb_q, parse_mode="HTML"
    )

@dp.callback_query(QuizStates.q1_age)
async def cb_quiz_age(callback: types.CallbackQuery, state: FSMContext):
    age_map = {"age_8_10": "8–10 лет", "age_11_13": "11–13 лет", "age_14_16": "14–16+ лет"}
    await state.update_data(age=age_map.get(callback.data, callback.data))
    await state.set_state(QuizStates.q2_games)

    kb_q = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="GTA 5, CS2, Гонки, Шутеры", callback_data="game_gta")],
        [InlineKeyboardButton(text="Roblox / Minecraft", callback_data="game_roblox")],
        [InlineKeyboardButton(text="Любит технику и конструкторы", callback_data="game_tech")],
        [InlineKeyboardButton(text="Мало играет / больше сидит в интернете", callback_data="game_web")]
    ])
    await callback.message.edit_text(
        "<b>Вопрос 2 из 4:</b> Во что ребенок больше всего играет за компьютером?",
        reply_markup=kb_q, parse_mode="HTML"
    )

@dp.callback_query(QuizStates.q2_games)
async def cb_quiz_games(callback: types.CallbackQuery, state: FSMContext):
    games_map = {
        "game_gta": "GTA 5 / Шутеры / Экшн",
        "game_roblox": "Roblox / Minecraft",
        "game_tech": "Техника и конструкторы",
        "game_web": "Мало играет в игры"
    }
    await state.update_data(games=games_map.get(callback.data, callback.data))
    await state.set_state(QuizStates.q3_exp)

    kb_q = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="С нуля, никогда не пробовал", callback_data="exp_zero")],
        [InlineKeyboardButton(text="Пробовал Scratch / визуальные блоки", callback_data="exp_scratch")],
        [InlineKeyboardButton(text="Пробовал писать код (Python / C#)", callback_data="exp_code")]
    ])
    await callback.message.edit_text(
        "<b>Вопрос 3 из 4:</b> Был ли уже опыт в программировании?",
        reply_markup=kb_q, parse_mode="HTML"
    )

@dp.callback_query(QuizStates.q3_exp)
async def cb_quiz_exp(callback: types.CallbackQuery, state: FSMContext):
    exp_map = {
        "exp_zero": "С нуля",
        "exp_scratch": "Scratch / Блочный код",
        "exp_code": "Пробовал писать код сам"
    }
    await state.update_data(exp=exp_map.get(callback.data, callback.data))
    await state.set_state(QuizStates.q4_goal)

    kb_q = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перевести игры в профессию и пользу", callback_data="goal_skill")],
        [InlineKeyboardButton(text="Сдать школьный проект по информатике на 5", callback_data="goal_school")],
        [InlineKeyboardButton(text="Создать свою первую законченную 3D-игру", callback_data="goal_game")],
        [InlineKeyboardButton(text="Развить логику и понимание работы ПК", callback_data="goal_logic")]
    ])
    await callback.message.edit_text(
        "<b>Вопрос 4 из 4:</b> Какая цель сейчас для вас в приоритете?",
        reply_markup=kb_q, parse_mode="HTML"
    )

@dp.callback_query(QuizStates.q4_goal)
async def cb_quiz_goal(callback: types.CallbackQuery, state: FSMContext):
    goal_map = {
        "goal_skill": "Превратить игры в пользу и профессию",
        "goal_school": "Школьный индивидуальный проект на 5",
        "goal_game": "Создать свою 3D-игру",
        "goal_logic": "Развить логику и понимание работы ПК"
    }
    await state.update_data(goal=goal_map.get(callback.data, callback.data))
    data = await state.get_data()

    # Track logic
    track = "Разработка 3D-игр в Unity & Моддинг на C#"
    if "Техника" in data.get("games", ""):
        track = "Робототехника и Схемотехника на Arduino"
    elif "Школьный" in data.get("goal", ""):
        track = "Индивидуальный школьный проект по информатике под ключ"
    elif "Мало играет" in data.get("games", ""):
        track = "Создание интерактивных сайтов и веб-разработка (Frontend)"

    await state.update_data(recommended_track=track)
    await state.set_state(QuizStates.get_contact)

    text = (
        f"🎯 <b>РЕЗУЛЬТАТ ПОДБОРА ПРОГРАММЫ:</b>\n\n"
        f"🏆 <b>Рекомендованный трек:</b> {track}\n\n"
        "Эта программа идеально совмещает горячий интерес ребенка и изучение реального синтаксиса программирования.\n\n"
        "🎁 <b>Запишитесь на бесплатный пробный урок (40 минут):</b>\n"
        "Мы познакомимся, напишем первый рабочий скрипт, и вы увидите реакцию ребенка.\n\n"
        "👇 Напишите в ответном сообщении: <b>имя ребенка + ваш контакт (телефон или оставьте этот Telegram)</b>:"
    )
    kb_q = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оставить только этот Telegram", callback_data="confirm_tg_contact")],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb_q, parse_mode="HTML")

@dp.callback_query(F.data == "confirm_tg_contact")
async def cb_confirm_tg(callback: types.CallbackQuery, state: FSMContext):
    await finish_booking(callback.message, callback.from_user, state, contact_info="Telegram профиль")

@dp.message(QuizStates.get_contact)
async def msg_get_contact(message: types.Message, state: FSMContext):
    contact_info = message.text.strip()
    await finish_booking(message, message.from_user, state, contact_info=contact_info)

@dp.callback_query(F.data == "book_trial")
async def cb_book_trial(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(QuizStates.get_contact)
    text = (
        "🎁 <b>Запись на бесплатный вводный урок (40 минут):</b>\n\n"
        "Занятие проходит онлайн в удобное для вас время. Ребенок напишет свой первый скрипт в игре/движке, а вы получите подробный разбор его способностей.\n\n"
        "👇 Напишите в ответном сообщении: <b>имя и возраст ребенка + ваш телефон для связи</b> (или нажмите кнопку ниже):"
    )
    kb_q = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оставить только этот Telegram", callback_data="confirm_tg_contact")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb_q, parse_mode="HTML")

async def finish_booking(message_target: types.Message, user: types.User, state: FSMContext, contact_info: str):
    data = await state.get_data()
    await state.clear()

    user_link = f"@{user.username}" if user.username else f"id: {user.id}"
    full_name = user.full_name or "Не указано"
    track = data.get("recommended_track", "Прямая запись на пробник")

    # Save to SQLite DB
    lead_id = db.create_lead(
        user_id=user.id,
        parent_name=full_name,
        kid_info=f"Возраст: {data.get('age', '—')}",
        contact=contact_info,
        track=track,
        answers=data
    )

    # Notification to Vadim (Admin)
    admin_text = (
        f"🔥 <b>НОВАЯ ЗАЯВКА НА ПРОБНЫЙ УРОК [#{lead_id}]!</b>\n\n"
        f"👤 <b>Пользователь:</b> {html.escape(full_name)} ({user_link})\n"
        f"📱 <b>Контакт:</b> {html.escape(contact_info)}\n\n"
        f"🎯 <b>Подобранный трек:</b> {track}\n"
        f"🎂 <b>Возраст:</b> {data.get('age', '—')}\n"
        f"🎮 <b>Игры:</b> {data.get('games', '—')}\n"
        f"💻 <b>Опыт:</b> {data.get('exp', '—')}\n"
        f"🎯 <b>Цель:</b> {data.get('goal', '—')}"
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            reply_markup=kb.get_lead_actions_keyboard(lead_id),
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка отправки уведомления админу: {e}")

    # Confirmation to Parent
    thanks_text = (
        "✅ <b>Заявка успешно принята!</b>\n\n"
        "Я (Вадим) свяжусь с вами в течение 15 минут прямо в Telegram, чтобы согласовать удобный день и время для бесплатного первого урока.\n\n"
        "До встречи на занятии!"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать Вадиму напрямую", url="https://t.me/mrvasilievv")]
    ])
    await message_target.answer(thanks_text, reply_markup=markup, parse_mode="HTML")

# --- ADMIN PANEL ---
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("⚙️ <b>Панель управления наставника:</b>", reply_markup=kb.get_admin_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "admin_panel")
async def cb_admin_panel(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.edit_text("⚙️ <b>Панель управления наставника:</b>", reply_markup=kb.get_admin_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    stats = db.get_stats()
    text = (
        "📊 <b>Аналитика и статистика бота:</b>\n\n"
        f"👥 Всего пользователей в базе: <b>{stats['users']}</b>\n"
        f"📥 Всего заявок (лидов): <b>{stats['leads']}</b>\n"
        f"🆕 Свежих заявок (NEW): <b>{stats['new_leads']}</b>\n"
        f"💰 Оплативших абонемент (PAID): <b>{stats['paid_leads']}</b>\n"
        f"🤝 Партнеров-репетиторов: <b>{stats['partners']}</b>\n"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад в админку", callback_data="admin_panel")]])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

@dp.callback_query(F.data.in_(["admin_leads_all", "admin_leads_new"]))
async def cb_admin_leads(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    status_filter = "NEW" if callback.data == "admin_leads_new" else None
    leads = db.get_leads(status=status_filter, limit=10)

    if not leads:
        text = "📭 Заявок с данным статусом пока нет."
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ В админку", callback_data="admin_panel")]])
        await callback.message.edit_text(text, reply_markup=markup)
        return

    text = f"📋 <b>Список заявок ({'Только новые' if status_filter else 'Все'}):</b>\n\n"
    kb_list = []
    for l in leads:
        lead_title = f"#{l['id']} | {l['parent_name'][:14]} [{l['status']}]"
        kb_list.append([InlineKeyboardButton(text=lead_title, callback_data=f"view_lead_{l['id']}")])
    kb_list.append([InlineKeyboardButton(text="◀️ В админку", callback_data="admin_panel")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_list), parse_mode="HTML")

@dp.callback_query(F.data.startswith("view_lead_"))
async def cb_view_lead(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    lead_id = int(callback.data.replace("view_lead_", ""))
    l = db.get_lead_by_id(lead_id)
    if not l:
        await callback.answer("Заявка не найдена!")
        return

    text = (
        f"📋 <b>Карточка заявки #{l['id']}</b>\n\n"
        f"👤 <b>Родитель:</b> {html.escape(l['parent_name'])}\n"
        f"📱 <b>Контакт:</b> {html.escape(l['contact'])}\n"
        f"👶 <b>Ребенок:</b> {html.escape(l['kid_info'])}\n"
        f"🎯 <b>Трек:</b> {html.escape(l['track'])}\n"
        f"🏷 <b>Статус:</b> <code>{l['status']}</code>\n"
        f"📅 <b>Дата:</b> {l['created_at']}"
    )
    await callback.message.edit_text(text, reply_markup=kb.get_lead_actions_keyboard(lead_id), parse_mode="HTML")

@dp.callback_query(F.data.startswith("lead_status_"))
async def cb_change_lead_status(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    parts = callback.data.split("_")
    lead_id = int(parts[2])
    new_status = parts[3]
    db.update_lead_status(lead_id, new_status)
    await callback.answer(f"Статус изменен на {new_status}!")
    
    # Refresh view
    l = db.get_lead_by_id(lead_id)
    text = (
        f"📋 <b>Карточка заявки #{l['id']}</b>\n\n"
        f"👤 <b>Родитель:</b> {html.escape(l['parent_name'])}\n"
        f"📱 <b>Контакт:</b> {html.escape(l['contact'])}\n"
        f"👶 <b>Ребенок:</b> {html.escape(l['kid_info'])}\n"
        f"🎯 <b>Трек:</b> {html.escape(l['track'])}\n"
        f"🏷 <b>Статус:</b> <code>{l['status']}</code>\n"
        f"📅 <b>Дата:</b> {l['created_at']}"
    )
    await callback.message.edit_text(text, reply_markup=kb.get_lead_actions_keyboard(lead_id), parse_mode="HTML")

# --- BROADCAST (РАССЫЛКА) ---
@dp.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(BroadcastStates.waiting_for_message)
    text = (
        "📢 <b>Режим рассылки сообщений:</b>\n\n"
        "Отправьте текст сообщения, который вы хотите разослать всем пользователям бота (поддерживается HTML-разметка).\n\n"
        "Для отмены отправьте /cancel."
    )
    await callback.message.edit_text(text, parse_mode="HTML")

@dp.message(BroadcastStates.waiting_for_message)
async def msg_broadcast_send(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Рассылка отменена.", reply_markup=kb.get_admin_keyboard())
        return

    await state.clear()
    user_ids = db.get_all_user_ids()
    sent_count = 0

    await message.answer(f"🚀 Начинаю рассылку по {len(user_ids)} пользователям...")
    for uid in user_ids:
        try:
            await bot.send_message(chat_id=uid, text=message.text, parse_mode="HTML")
            sent_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await message.answer(f"✅ Рассылка завершена! Успешно доставлено: {sent_count} из {len(user_ids)}.", reply_markup=kb.get_admin_keyboard())

# --- MAIN RUNNER ---
async def on_startup(bot: Bot):
    try:
        from aiogram.types import BotCommandScopeDefault, BotCommandScopeChat
        
        # 1. Для всех клиентов (родителей и детей) — только клиентские команды
        await bot.set_my_commands([
            types.BotCommand(command="start", description="🚀 Главное меню студии"),
            types.BotCommand(command="app", description="✨ Интерактивная Web-витрина"),
            types.BotCommand(command="quiz", description="🎯 Подобрать программу (40 сек)")
        ], scope=BotCommandScopeDefault())
        
        # 2. Только в личном чате Вадима — панель управления CRM
        await bot.set_my_commands([
            types.BotCommand(command="start", description="🚀 Главное меню студии"),
            types.BotCommand(command="app", description="✨ Интерактивная Web-витрина"),
            types.BotCommand(command="admin", description="⚙️ CRM & Управление заявками")
        ], scope=BotCommandScopeChat(chat_id=ADMIN_ID))

        await bot.set_my_short_description("🎮 Индивидуальные уроки создания 3D-игр в Unity и C# моддинга в GTA 5 для ребят 8–16 лет.")
        await bot.set_my_description(
            "👋 Добро пожаловать в персональную IT-студию Вадима Васильева!\n\n"
            "Здесь дети 8–16 лет создают свои игры на Unity 3D, пишут скрипты на C# в GTA 5 и готовят школьные проекты под ключ.\n\n"
            "Нажмите СТАРТ или запустите Web App, чтобы подобрать персональную программу обучения!"
        )
    except Exception as e:
        logging.warning(f"Metadata setup warning: {e}")

async def main():
    logging.info("🚀 Дизайнерский бот-комбайн Вадима запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await on_startup(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
