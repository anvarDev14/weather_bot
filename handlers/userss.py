from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from keyboards.default.menu import get_language_keyboard, get_main_menu_uz, get_main_menu_ru
from database.db import user_db
from utils.weather import get_weather, get_weather_by_location, get_weekly_forecast
from utils.advertising import Advertisement  # Импорт класса Advertisement
import datetime
import asyncio

# Список администраторов (можно вынести в config.py)
ADMINS = [6369838846]  # Ваш Telegram ID


# Состояния FSM
class UserStates(StatesGroup):
    waiting_city = State()
    waiting_language = State()
    waiting_ad_content = State()  # Для ввода текста рекламы


def setup(dp: Dispatcher):
    @dp.message_handler(commands=["start"])
    async def start_command(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        username = message.from_user.username or "NoUsername"
        join_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not user_db.user_exists(user_id):
            user_db.add_user(user_id, username, join_date)
            from handlers.notifications import notify_admin_new_user
            await notify_admin_new_user(dp.bot, user_id, username)
            print(f"New user {user_id} added, asking for language")
            await message.answer("Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
                                 reply_markup=get_language_keyboard())
            await UserStates.waiting_language.set()
        else:
            language = user_db.get_user_language(user_id)
            if language not in ["uz", "ru"]:
                print(f"User {user_id} has no valid language, asking for language")
                await message.answer("Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
                                     reply_markup=get_language_keyboard())
                await UserStates.waiting_language.set()
            else:
                print(f"User {user_id} already has language {language}, showing main menu")
                welcome_text = "Xush kelibsiz! Men ob-havo botiman." if language == "uz" else "Добро пожаловать! Я бот погоды."
                keyboard = get_main_menu_uz() if language == "uz" else get_main_menu_ru()
                await message.answer(welcome_text, reply_markup=keyboard)

    @dp.message_handler(lambda message: message.text in ["🇺🇿 O'zbekcha", "🇷🇺 Русский"],
                        state=UserStates.waiting_language)
    async def process_language(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        language = "uz" if message.text == "🇺🇿 O'zbekcha" else "ru"
        user_db.update_language(user_id, language)
        welcome_text = "Xush kelibsiz! Men ob-havo botiman." if language == "uz" else "Добро пожаловать! Я бот погоды."
        keyboard = get_main_menu_uz() if language == "uz" else get_main_menu_ru()
        print(f"User {user_id} selected language {language}, showing main menu")
        await message.answer(welcome_text, reply_markup=keyboard)
        await state.finish()

    @dp.message_handler(content_types=types.ContentType.LOCATION)
    async def weather_by_location(message: types.Message):
        user_id = message.from_user.id
        language = user_db.get_user_language(user_id)
        lat = message.location.latitude
        lon = message.location.longitude
        weather = await get_weather_by_location(lat, lon, language)
        keyboard = get_main_menu_uz() if language == "uz" else get_main_menu_ru()
        print(f"User {user_id} requested weather by location")
        await message.answer(weather, reply_markup=keyboard)

    @dp.message_handler(lambda message: message.text in ["⛅ Hozirgi ob-havo", "⛅ Погода сейчас"])
    async def weather_now(message: types.Message):
        user_id = message.from_user.id
        language = user_db.get_user_language(user_id)
        city = user_db.get_user_location(user_id)
        weather = await get_weather(city, language)
        print(f"User {user_id} requested current weather for {city}")
        await message.answer(weather)

    @dp.message_handler(lambda message: message.text in ["📅 Haftalik prognoz", "📅 Прогноз на неделю"])
    async def weather_forecast(message: types.Message):
        user_id = message.from_user.id
        language = user_db.get_user_language(user_id)
        city = user_db.get_user_location(user_id)
        forecast = await get_weekly_forecast(city, language)
        print(f"User {user_id} requested weekly forecast for {city}")
        await message.answer(forecast)

    @dp.message_handler(lambda message: message.text in ["🌆 Shaharni o'zgartirish", "🌆 Изменить город"])
    async def change_city(message: types.Message):
        user_id = message.from_user.id
        language = user_db.get_user_language(user_id)
        text = "Iltimos, shahar nomini kiriting:" if language == "uz" else "Пожалуйста, введите название города:"
        print(f"User {user_id} requested to change city")
        await message.answer(text)
        await UserStates.waiting_city.set()

    @dp.message_handler(state=UserStates.waiting_city)
    async def process_city(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        language = user_db.get_user_language(user_id)
        city = message.text
        user_db.update_location(user_id, city)
        weather = await get_weather(city, language)
        keyboard = get_main_menu_uz() if language == "uz" else get_main_menu_ru()
        print(f"User {user_id} changed city to {city}")
        await message.answer(
            f"Shahar {city} ga o'zgartirildi.\n{weather}" if language == "uz" else f"Город изменен на {city}.\n{weather}",
            reply_markup=keyboard)
        await state.finish()

    @dp.message_handler(lambda message: message.text in ["🌐 Tilni o'zgartirish", "🌐 Сменить язык"])
    async def change_language(message: types.Message):
        print(f"User {message.from_user.id} requested to change language")
        await message.answer("Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
                             reply_markup=get_language_keyboard())
        await UserStates.waiting_language.set()

    # Команда /reklama
    @dp.message_handler(commands=["reklama"])
    async def reklama_handler(message: types.Message):
        user_id = message.from_user.id
        if user_id not in ADMINS:
            language = user_db.get_user_language(user_id)
            await message.reply("Sizda ruxsat yo'q." if language == "uz" else "У вас нет прав.")
            return
        language = user_db.get_user_language(user_id)
        await message.reply("Reklama matnini yuboring:" if language == "uz" else "Отправьте текст рекламы:")
        await UserStates.waiting_ad_content.set()

    # Обработка текста рекламы
    @dp.message_handler(state=UserStates.waiting_ad_content)
    async def process_ad_content(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        if user_id not in ADMINS:
            language = user_db.get_user_language(user_id)
            await message.reply("Sizda ruxsat yo'q." if language == "uz" else "У вас нет прав.")
            await state.finish()
            return

        ad_text = message.text
        ad_id = len([ad for ad in dir() if "advertisement" in ad.lower()]) + 1  # Простой счетчик для ID
        advertisement = Advertisement(ad_id=ad_id, message=ad_text, ad_type="ad_type_text", bot=dp.bot,
                                      creator_id=user_id)
        language = user_db.get_user_language(user_id)
        await message.reply(
            f"Reklama #{ad_id} jadvalga qo'shildi." if language == "uz" else f"Реклама #{ad_id} добавлена в расписание.")
        await asyncio.create_task(advertisement.start())
        await state.finish()