from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton



def get_forecast_buttons(lat,lon):
    markup=InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text='5 kunlik ',callback_data=f'forecast_5_{lat}_{lon}'),
        InlineKeyboardButton(text='xaftalik ',callback_data=f'forecast_7_{lat}_{lon}'),
        InlineKeyboardButton(text='10 kunlik ',callback_data=f'forecast_10_{lat}_{lon}')
    )
    return markup


