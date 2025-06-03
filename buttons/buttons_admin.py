from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
admin_kb=ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='Создать встречу'), KeyboardButton(text='Отменить/перенести')],
        [KeyboardButton(text='Все встречи'), KeyboardButton(text='Расписание встреч')],
        [KeyboardButton(text='Встречи на сегодня'), KeyboardButton(text='Удалить все встречи')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Чем могу быть полезен?')


change_kb=ReplyKeyboardMarkup(keyboard=[
          [KeyboardButton(text='Изменить время'),
            KeyboardButton(text='Изменить дату')],
            [KeyboardButton(text='Удалить встречу'),
            KeyboardButton(text='Назад')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Чем могу быть полезен?'
)


confirm_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Да ✅"), KeyboardButton(text="Нет ❌")]
    ],
    resize_keyboard=True,
    input_field_placeholder='Чем могу быть полезен?')

back_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True,
    input_field_placeholder='Чем могу быть полезен?')