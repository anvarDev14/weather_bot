import os
from datetime import datetime

import requests
from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.types import CallbackQuery
from keyboards.default.menu import menu_start
from keyboards.inline.weather_buttons import get_forecast_buttons
from loader import dp
WEATHER_API_KEY = os.getenv('8aab62712df12fec699d40dc4c82467d')


def fetch_weather_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


def format_weather_response(data, days=None):
    if not data or 'daily' not in data:
        return "❌Kunlik ob-havo ma'lumotlari mavjud emas."

    answer = ""
    for i in range(days or 1):
        today = data['daily']['time'][i]
        temp_max = data['daily']['temperature_2m_max'][i]
        temp_min = data['daily']['temperature_2m_min'][i]
        precipitation = data['daily']['precipitation_sum'][i]
        win_speed = data['daily']['windspeed_10m_max'][i]

        answer += (
            f"\n🗓**Sana:** {today}\n"
            f"🔼**Eng yuqori harorat:** {temp_max}°C\n"
            f"🔼**Eng past harorat:** {temp_min}°C\n"
            f"☁️**Yog'ingarchilik:** {precipitation}\n"
            f"💨**Shamol tezligi:** {win_speed}\n"
        )
    return answer


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    await message.answer("Assalomu alaykum Ob-havo botiga xush kelibsiz", reply_markup=menu_start)


@dp.message_handler(content_types=types.ContentType.LOCATION)
async def location_addres_function(message: types.Message):
    lon, lat = message.location.longitude, message.location.latitude
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max&timezone=auto"

    data = fetch_weather_data(url)
    answer = format_weather_response(data)

    await message.answer(answer, parse_mode="Markdown", reply_markup=get_forecast_buttons(lat, lon))


@dp.callback_query_handler(lambda c: c.data.startswith('forecast_'))
async def buttons_callback_text(callback_query: CallbackQuery):
    _, days, lat, lon = callback_query.data.split('_')
    days = int(days)

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max&timezone=auto"

    data = fetch_weather_data(url)
    answer = format_weather_response(data, days)

    await callback_query.message.answer(answer, parse_mode="Markdown", reply_markup=get_forecast_buttons(lat, lon))


def get_weather(city):
    url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}'
    response = requests.get(url)
    return response.json()



@dp.message_handler(commands='weather')
async def send_welcome(message: types.Message):
    await message.reply(
        f"<b>Assalomu alaykum {message.from_user.first_name}! \nIstalgan shahar nomini kiriting: </b>",
        parse_mode='HTML'
    )


@dp.message_handler()
async def get_weather(message: types.Message, ob_havo_Token='8aab62712df12fec699d40dc4c82467d'):

    try:
        r = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={message.text}&appid={ob_havo_Token}&units=metric"
        )
        data = r.json()
        shahar = data["name"]
        harorat = data["main"]["temp"]
        namlik = data["main"]["humidity"]
        bosim = data["main"]["pressure"]
        shamol = data["wind"]["speed"]
        quyosh_chiqishi = datetime.fromtimestamp(data["sys"]["sunrise"])
        quyosh_botishi = datetime.fromtimestamp(data["sys"]["sunset"])
        kunning_uzunligi = quyosh_botishi - quyosh_chiqishi

        await message.reply(
            f"<b>Xozirgi Vaqt Bo'yicha ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n"
            f"{shahar} shahar ob-havosi!\nHarorat: {harorat}°C\n"
            f"Namlik: {namlik}💦%\nBosim: {bosim} mm sim. ust\nShamol: {shamol}🌬m/s\n"
            f"Quyosh chiqishi: {quyosh_chiqishi}🌇\nQuyosh botishi: {quyosh_botishi}🌅\nKunning uzunligi: {kunning_uzunligi}⏳\n"
            f"\nSalomat bo'ling! 👋🏻</b>", parse_mode='HTML'
        )
    except Exception as e:
        await message.reply(f'Shahar nomi topilmadi: 😣{str(e)} \U0001F642')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
