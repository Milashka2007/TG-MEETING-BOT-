from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
start_kb=ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Профиль'),
            KeyboardButton(text='Записаться на встречу'),
            KeyboardButton(text='Отменить запись'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder='Чем могу быть полезен?'
)
profile=ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Изменить имя'),
            KeyboardButton(text='В меню'),
            KeyboardButton(text='Мои записи'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder='Чем могу быть полезен?'
)

back_kb=ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='В меню'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder='Чем могу быть полезен?'
)

