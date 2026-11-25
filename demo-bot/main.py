import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import config
import database
import keyboards

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

class BookingFlow(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    custom_date = State()
    entering_name = State()
    entering_phone = State()

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        f"👋 **Здравствуйте, {message.from_user.first_name}!**\n\n"
        "Добро пожаловать в сервис онлайн-записи и консультаций.\n"
        "Здесь вы можете выбрать удобное время, рассчитать стоимость и забронировать визит за 1 минуту.\n\n"
        "👇 *Выберите нужный раздел в меню ниже:*"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=keyboards.get_main_menu())

@dp.callback_query(F.data == "back_to_main")
async def cb_back_to_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "Главное меню сервиса. Чем можем помочь?",
        reply_markup=keyboards.get_main_menu()
    )
    await call.answer()

@dp.callback_query(F.data == "catalog")
async def cb_catalog(call: CallbackQuery):
    text = "📋 **Прайс-лист наших услуг:**\n\n"
    for _, srv in config.SERVICES.items():
        text += f"🔹 **{srv['name']}**\n   ⏱ Длительность: {srv['duration']}\n   💰 Стоимость: {srv['price']} ₽\n\n"
    text += "Нажмите «Записаться», чтобы забронировать время."
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboards.get_services_keyboard())
    await call.answer()

@dp.callback_query(F.data == "contacts")
async def cb_contacts(call: CallbackQuery):
    text = (
        "📍 **Контакты и информация:**\n\n"
        "🏢 Адрес: г. Москва, ул. Примерная, 10\n"
        "⏰ График: Ежедневно с 09:00 до 21:00\n"
        "📞 Телефон: +7 (999) 000-00-00\n"
        "💬 Менеджер: @telegram_username\n\n"
        "_Бот работает 24/7 и принимает заявки круглосуточно._"
    )
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboards.get_main_menu())
    await call.answer()

@dp.callback_query(F.data == "ask_question")
async def cb_ask_question(call: CallbackQuery):
    await call.message.edit_text(
        "По всем индивидуальным вопросам вы можете написать напрямую нашему администратору: @telegram_username\nЛибо оставьте заявку на запись, и мы перезвоним!",
        reply_markup=keyboards.get_main_menu()
    )
    await call.answer()

@dp.callback_query(F.data == "start_booking")
async def cb_start_booking(call: CallbackQuery, state: FSMContext):
    await state.set_state(BookingFlow.choosing_service)
    await call.message.edit_text(
        "Шаг 1 из 3: Выберите желаемую услугу:",
        reply_markup=keyboards.get_services_keyboard()
    )
    await call.answer()

@dp.callback_query(BookingFlow.choosing_service, F.data.startswith("book_"))
async def cb_service_chosen(call: CallbackQuery, state: FSMContext):
    srv_id = call.data.replace("book_", "")
    srv_data = config.SERVICES.get(srv_id)
    if not srv_data:
        await call.answer("Услуга не найдена", show_alert=True)
        return
    await state.update_data(service_name=srv_data["name"], service_price=srv_data["price"])
    await state.set_state(BookingFlow.choosing_date)
    await call.message.edit_text(
        f"Выбрано: **{srv_data['name']}** ({srv_data['price']} ₽)\n\n"
        "Шаг 2 из 3: Выберите подходящее время или укажите своё:",
        parse_mode="Markdown",
        reply_markup=keyboards.get_dates_keyboard()
    )
    await call.answer()

@dp.callback_query(BookingFlow.choosing_date, F.data.startswith("date_"))
async def cb_date_chosen(call: CallbackQuery, state: FSMContext):
    chosen_date = call.data.replace("date_", "")
    if chosen_date == "custom":
        await state.set_state(BookingFlow.custom_date)
        await call.message.edit_text("Напишите желаемую дату и время в ответном сообщении (например: `В пятницу после 18:00`):", parse_mode="Markdown")
        await call.answer()
        return

    await state.update_data(date_time=chosen_date)
    await state.set_state(BookingFlow.entering_name)
    await call.message.edit_text("Шаг 3 из 3: Как к вам обращаться? (Введите ваше имя):")
    await call.answer()

@dp.message(BookingFlow.custom_date)
async def process_custom_date(message: Message, state: FSMContext):
    await state.update_data(date_time=message.text)
    await state.set_state(BookingFlow.entering_name)
    await message.answer("Шаг 3 из 3: Как к вам обращаться? (Введите ваше имя):")

@dp.message(BookingFlow.entering_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(BookingFlow.entering_phone)
    await message.answer(
        "Отлично! Последний шаг — отправьте ваш контактный номер телефона для подтверждения записи:",
        reply_markup=keyboards.get_phone_request_keyboard()
    )

@dp.message(BookingFlow.entering_phone)
async def process_phone(message: Message, state: FSMContext):
    if message.text == "Отмена":
        await state.clear()
        await message.answer("Запись отменена.", reply_markup=ReplyKeyboardRemove())
        await message.answer("Главное меню:", reply_markup=keyboards.get_main_menu())
        return

    phone = message.contact.phone_number if message.contact else message.text
    data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username or ""
    full_name = data.get("full_name", message.from_user.full_name)
    service_name = data.get("service_name", "Не указана")
    service_price = data.get("service_price", 0)
    date_time = data.get("date_time", "Уточняется")

    # Сохраняем в локальную БД
    booking_id = database.add_booking(
        user_id=user_id,
        username=username,
        full_name=full_name,
        service_name=service_name,
        service_price=service_price,
        date_time=date_time,
        phone=phone
    )

    await state.clear()

    # Клиенту
    success_text = (
        f"✅ **Заявка №{booking_id} успешно создана!**\n\n"
        f"👤 **Имя:** {full_name}\n"
        f"📱 **Телефон:** {phone}\n"
        f"🛠 **Услуга:** {service_name}\n"
        f"💰 **Стоимость:** {service_price} ₽\n"
        f"📅 **Время:** {date_time}\n\n"
        "Мы свяжемся с вами в течение 10 минут для подтверждения!"
    )
    await message.answer(success_text, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    await message.answer("Возврат в меню:", reply_markup=keyboards.get_main_menu())

    # Уведомление администратору (если задан)
    if config.ADMIN_ID and config.ADMIN_ID != 0:
        admin_alert = (
            f"🔔 **НОВАЯ ЗАЯВКА #{booking_id}**\n\n"
            f"👤 Клиент: {full_name} (@{username})\n"
            f"📱 Телефон: `{phone}`\n"
            f"🛠 Услуга: {service_name}\n"
            f"💰 Сумма: {service_price} ₽\n"
            f"📅 Желаемое время: {date_time}"
        )
        try:
            await bot.send_message(chat_id=config.ADMIN_ID, text=admin_alert, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление админу ({config.ADMIN_ID}): {e}")

@dp.message(Command("setadmin"))
async def cmd_setadmin(message: Message):
    config.ADMIN_ID = message.from_user.id
    # Обновляем .env файл
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        with open(env_path, "w") as f:
            f.write(f"BOT_TOKEN={config.BOT_TOKEN}\nADMIN_ID={message.from_user.id}\n")
    except Exception as e:
        logging.error(f"Ошибка сохранения .env: {e}")
    await message.answer(
        f"👑 **Вы успешно назначены администратором бота!**\n\n"
        f"Ваш Telegram ID: `{message.from_user.id}`\n"
        f"Теперь все новые заявки от клиентов будут мгновенно приходить сюда.\n"
        f"Команда `/admin` откроет вам статистику и панель управления.",
        parse_mode="Markdown"
    )

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if config.ADMIN_ID and message.from_user.id != config.ADMIN_ID:
        await message.answer("Доступ к панели управления ограничен. Отправьте /setadmin для привязки вашего аккаунта.")
        return

    count, total = database.get_stats()
    recent = database.get_all_bookings(5)

    text = f"📊 **Панель управления заказами**\n\n"
    text += f"Всего заявок: **{count}**\n"
    text += f"Потенциальная выручка: **{total:,} ₽**\n\n".replace(",", " ")
    text += "Последние записи:\n"
    for r in recent:
        text += f"• #{r[0]} | {r[1]} | {r[2]} | {r[3]} ({r[4]} ₽) | {r[5]}\n"

    await message.answer(text, parse_mode="Markdown")

async def main():
    database.init_db()
    if not config.BOT_TOKEN:
        print("\n" + "="*60)
        print("ВНИМАНИЕ: Токен бота не указан в .env файле!")
        print("Создайте бота через @BotFather в Telegram и вставьте токен в .env")
        print("="*60 + "\n")
        return
    print(f"[*] Демо-бот успешно запущен! Ожидание сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
