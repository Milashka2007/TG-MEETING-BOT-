from aiogram import types, Router, F, Bot
from aiogram.filters import CommandStart

from buttons.buttons_user import start_kb, profile, back_kb
from database.database import Database
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID

user_router = Router()
db = Database('fio.db')

class SelectMeet(StatesGroup):
    select_meet = State()

class Registration(StatesGroup):
    name = State()
    birthday = State()
    rename = State()

class CancelMeet(StatesGroup):
    select_to_cancel = State()

@user_router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    if not db.user_exists(message.from_user.id):
        db.add_user(message.from_user.id)
        await message.answer('Представьтесь пожалуйста, напишите свою фамилию и имя 🤝')
        await state.set_state(Registration.name)
    else:
        user_info = db.get_user_info(message.from_user.id)
        await message.answer(
            f'Здравствуйте, {user_info["nickname"]}!\n'
            f'Вы в главном меню!\n\n'
            f'Я бот секретарь, буду рад помочь вам записаться на встречу с супервайзером.',
            reply_markup=start_kb
        )

@user_router.message(Registration.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer('Теперь введите дату рождения в формате ДД.ММ.ГГГГ')
    await state.set_state(Registration.birthday)

@user_router.message(Registration.birthday)
async def get_birthday(message: types.Message, state: FSMContext):
    birth = message.text
    if birth.count('.') == 2:
        list_birth = birth.split('.')
        if (int(list_birth[0]) <= 31 and int(list_birth[1]) <= 12 and 
            len(list_birth[0]) == 2 and len(list_birth[1]) == 2 and 
            len(list_birth[2]) == 4):
            
            await state.update_data(birthday=birth)
            registration = await state.get_data()
            
            db.set_nickname(message.from_user.id, registration['name'])
            db.set_birthday(message.from_user.id, registration['birthday'])
            
            await message.answer(
                'Приятно познакомиться, регистрация прошла успешно.\n\n'
                'Теперь вы можете записаться на встречу, выбрав соответствующую клавишу в меню⬇️⬇️⬇️',
                reply_markup=start_kb
            )
            await state.clear()
        else:
            await message.answer('Некорректная дата')
    else:
        await message.answer('Неправильный формат ввода данных!')
        await state.set_state(Registration.birthday)

@user_router.message(F.text=='Мои записи')
async def show_meetings(message: types.Message):
    meetings = db.get_user_meetings(message.from_user.id)
    
    if not meetings:
        await message.answer('У вас пока нет записей', reply_markup=start_kb)
        return
    
    message_to_answer = ''
    for meeting in meetings:
        message_to_answer += (
            f'Встреча №{meeting["id"]}\n'
            f'Дата: {meeting["date"]}\n'
            f'Время: {meeting["time"]}\n\n'
        )
    
    await message.answer(message_to_answer, reply_markup=start_kb)

@user_router.message(F.text=='Профиль')
async def profil(message: types.Message):
    user_nickname = 'Ваше имя: ' + str(db.get_nickname(message.from_user.id))
    await message.answer(user_nickname, reply_markup=profile)

@user_router.message(F.text=='Отменить запись')
async def no_zapis(message: types.Message, state: FSMContext, bot: Bot):
    user_meetings = db.get_user_meetings(message.from_user.id)

    if not user_meetings:
        await message.answer('У вас нет активных записей для отмены.', reply_markup=start_kb)
        return

    if len(user_meetings) == 1:
        meeting_id_to_cancel = user_meetings[0]['id']
        user_id = message.from_user.id
        user_info = db.get_user_info(user_id)

        if db.cancel_meeting(meeting_id_to_cancel):
            await message.answer(f'Запись на встречу №{meeting_id_to_cancel} успешно отменена!', reply_markup=start_kb)
        else:
            await message.answer('Не удалось отменить запись.', reply_markup=start_kb)

        await state.clear()

    else:
        message_to_answer = 'Выберите номер встречи, которую хотите отменить:\n\n'
        for meeting in user_meetings:
            message_to_answer += (
                f'Встреча №{meeting["id"]}\n'
                f'Дата: {meeting["date"]}\n'
                f'Время: {meeting["time"]}\n\n'
            )

        await message.answer(message_to_answer)
        await state.set_state(CancelMeet.select_to_cancel)

@user_router.message(CancelMeet.select_to_cancel, F.text)
async def process_cancel_meet(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    meeting_id = message.text
    
    try:
        meeting_id = int(meeting_id)
    except ValueError:
        await message.answer('Пожалуйста, введите числовой номер встречи.')
        return
        
    meeting = db.get_meeting(meeting_id)
    if not meeting or meeting['client_id'] != db.get_internal_user_id(user_id):
        await message.answer('Встреча с таким номером не найдена среди ваших записей.')
        return
        
    db.cancel_meeting(meeting_id)
    await message.answer(f'Запись на встречу №{meeting_id} успешно отменена!', reply_markup=start_kb)
    
    await bot.send_message(ADMIN_ID, f'Пользователь {message.from_user.full_name} отменил запись на встречу №{meeting_id} ({meeting['date']} в {meeting['time']}).')
    
    await state.clear()

@user_router.message(F.text=='Изменить имя')
async def changenick(message: types.Message, state: FSMContext):
    await message.answer('напишите ваше ФИ')
    await state.set_state(Registration.rename)

@user_router.message(Registration.rename)
async def changenick1(message: types.Message, state: FSMContext):
    nickname = message.text
    if len(nickname.split())==2:
        if nickname.split()[0].isalpha()==True and nickname.split()[1].isalpha()==True:
            await state.update_data(rename=nickname)
            name=await state.get_data()
            nickname=name['rename']
            old_name=db.get_nickname(message.from_user.id)
            db.change_user_nickname(nickname, old_name)
            await message.answer(f'Поздравляю! Теперь вас зовут {nickname}', reply_markup=start_kb)
            await state.clear()
        else:
            await message.answer('Вы должны использовать только символы киррилицы!')
            await state.set_state(Registration.rename)
    else:
        await message.answer('Введите фамилию и имя!')

@user_router.message(F.text=='В меню')
async def menu(message: types.Message):
    await message.answer('Перевожу вас в главное меню!', reply_markup=start_kb)

@user_router.message(F.text=='Записаться на встречу')
async def zapis(message: types.Message, state: FSMContext):
    user_meetings = db.get_user_meetings(message.from_user.id)

    if user_meetings:
        message_to_answer = 'У вас уже есть запланированные встречи:\n\n'
        for meeting in user_meetings:
             message_to_answer += (
                f'Встреча №{meeting["id"]}\n'
                f'Дата: {meeting["date"]}\n'
                f'Время: {meeting["time"]}\n\n'
            )
        message_to_answer += 'Пожалуйста, отмените текущую запись перед тем, как записаться на новую.'
        await message.answer(message_to_answer, reply_markup=start_kb)
    else:
        available_meetings = db.get_available_meetings()

        if not available_meetings:
            await message.answer('На данный момент нет доступных встреч для записи.', reply_markup=start_kb)
            return

        message_to_answer = 'Выберите номер встречи для записи:\n\n'
        for meeting in available_meetings:
            message_to_answer += (
                f'Встреча №{meeting["id"]}\n'
                f'Дата: {meeting["date"]}\n'
                f'Время: {meeting["time"]}\n\n'
            )

        await message.answer(message_to_answer)
        await state.set_state(SelectMeet.select_meet)

@user_router.message(SelectMeet.select_meet, F.text)
async def book_meeting(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(select_meet=message.text)
    chose = message.text
    
    try:
        meeting_id = int(chose)
    except ValueError:
        await message.answer('Пожалуйста, введите числовой номер встречи.')
        await state.clear()
        return

    meeting = db.get_meeting(meeting_id)
    if not meeting:
        await message.answer('Такой встречи нет(')
        await state.clear()
        return

    if meeting['status'] != 'Можно записаться':
        await message.answer('На эту встречу мест нет')
        await state.clear()
        return

    user_meetings = db.get_user_meetings(message.from_user.id)
    if user_meetings:
        await message.answer('У вас уже есть запланированная встреча. Пожалуйста, отмените ее сначала.', reply_markup=start_kb)
        await state.clear()
        return

    if db.book_meeting(meeting_id, message.from_user.id):
        user_info = db.get_user_info(message.from_user.id)
        await message.answer(
            f'Вы успешно записаны на встречу №{meeting_id} на {meeting["date"]} в {meeting["time"]}',
            reply_markup=start_kb
        )
        await bot.send_message(
            ADMIN_ID,
            f'{user_info["nickname"]} записался на встречу №{meeting_id} на {meeting["date"]} в {meeting["time"]}'
        )

        await state.clear()
        return

    else:
        await message.answer('Не удалось записаться на встречу')
        await state.clear()

@user_router.message()
async def bot_message(message: types.Message):
    await message.answer('Не знаю чего вы хотите, идите лучше в главное меню', reply_markup=start_kb)