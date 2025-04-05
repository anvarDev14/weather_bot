from aiogram import types

def get_ad_type_keyboard(language="uz"):
    keyboard = types.InlineKeyboardMarkup()
    if language == "uz":
        keyboard.add(types.InlineKeyboardButton("Matnli", callback_data="ad_type_text"))
        keyboard.add(types.InlineKeyboardButton("Forward", callback_data="ad_type_forward"))
        keyboard.add(types.InlineKeyboardButton("Tugmali", callback_data="ad_type_button"))
        keyboard.add(types.InlineKeyboardButton("Har qanday kontent", callback_data="ad_type_any"))
    else:  # ru
        keyboard.add(types.InlineKeyboardButton("Текстовое", callback_data="ad_type_text"))
        keyboard.add(types.InlineKeyboardButton("Пересланное", callback_data="ad_type_forward"))
        keyboard.add(types.InlineKeyboardButton("С кнопками", callback_data="ad_type_button"))
        keyboard.add(types.InlineKeyboardButton("Любой контент", callback_data="ad_type_any"))
    return keyboard

def get_time_keyboard(language="uz"):
    keyboard = types.InlineKeyboardMarkup()
    if language == "uz":
        keyboard.add(types.InlineKeyboardButton("Hozir", callback_data="send_now"))
        keyboard.add(types.InlineKeyboardButton("Keyingi vaqt", callback_data="send_later"))
    else:  # ru
        keyboard.add(types.InlineKeyboardButton("Сейчас", callback_data="send_now"))
        keyboard.add(types.InlineKeyboardButton("Позже", callback_data="send_later"))
    return keyboard

def get_cancel_keyboard(language="uz"):
    keyboard = types.InlineKeyboardMarkup()
    text = "❌ Bekor qilish" if language == "uz" else "❌ Отменить"
    keyboard.add(types.InlineKeyboardButton(text, callback_data="cancel_ad"))
    return keyboard

def get_confirm_keyboard(language="uz"):
    keyboard = types.InlineKeyboardMarkup()
    confirm_text = "✅ Tasdiqlash" if language == "uz" else "✅ Подтвердить"
    cancel_text = "❌ Bekor qilish" if language == "uz" else "❌ Отменить"
    keyboard.add(types.InlineKeyboardButton(confirm_text, callback_data="confirm_ad"))
    keyboard.add(types.InlineKeyboardButton(cancel_text, callback_data="cancel_ad"))
    return keyboard

def get_status_keyboard(ad_id, paused=False, language="uz"):
    keyboard = types.InlineKeyboardMarkup()
    if language == "uz":
        if paused:
            keyboard.add(types.InlineKeyboardButton("▶️ Davom ettirish", callback_data=f"resume_ad_{ad_id}"))
        else:
            keyboard.add(types.InlineKeyboardButton("⏸️ Pauza", callback_data=f"pause_ad_{ad_id}"))
        keyboard.add(types.InlineKeyboardButton("⛔️ To'xtatish", callback_data=f"stop_ad_{ad_id}"))
    else:  # ru
        if paused:
            keyboard.add(types.InlineKeyboardButton("▶️ Продолжить", callback_data=f"resume_ad_{ad_id}"))
        else:
            keyboard.add(types.InlineKeyboardButton("⏸️ Пауза", callback_data=f"pause_ad_{ad_id}"))
        keyboard.add(types.InlineKeyboardButton("⛔️ Остановить", callback_data=f"stop_ad_{ad_id}"))
    return keyboard