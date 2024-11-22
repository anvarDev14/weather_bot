from aiogram.types import ReplyKeyboardMarkup,KeyboardButton


menu_start=ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='📍Manzil',request_location=True),
        ],
    ],
    resize_keyboard=True
)

