from aiogram import types

def get_language_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("🇺🇿 O'zbekcha"), types.KeyboardButton("🇷🇺 Русский"))
    return keyboard

def get_main_menu_uz():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("📍 Prognoz bo'yicha geolokatsiya", request_location=True))
    keyboard.add(types.KeyboardButton("⛅ Hozirgi ob-havo"), types.KeyboardButton("📅 Haftalik prognoz"))
    keyboard.add(types.KeyboardButton("🌆 Shaharni o'zgartirish"), types.KeyboardButton("🌐 Tilni o'zgartirish"))
    return keyboard

def get_main_menu_ru():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("📍 Прогноз по геолокации", request_location=True))
    keyboard.add(types.KeyboardButton("⛅ Погода сейчас"), types.KeyboardButton("📅 Прогноз на неделю"))
    keyboard.add(types.KeyboardButton("🌆 Изменить город"), types.KeyboardButton("🌐 Сменить язык"))
    return keyboard