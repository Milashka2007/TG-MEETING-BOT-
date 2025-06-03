from buttons.calendar import calendar_month, calendar_day, calendar_time
from aiogram import Router, types, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery
from datetime import *
from aiogram.fsm.state import State, StatesGroup
from buttons.buttons_admin import admin_kb, change_kb, confirm_kb, back_kb
from aiogram.fsm.context import FSMContext
from random import choice
from database.database import Database
from aiogram.types import ReplyKeyboardRemove
from config import ADMINS, ADMIN_ID

db = Database('fio.db')
admin_router = Router()

class AddMeet(StatesGroup):
    day = State()
    time = State()
    month = State()

class ChangeMeet(StatesGroup):
    month = State()
    day = State()
    time = State()
    vvod = State()

class Confirm(StatesGroup):
    da_net = State()

@admin_router.message(CommandStart())
async def admin_start(message: types.Message):
    if message.from_user.id in ADMINS:
        await message.answer('Здравствуйте, вы в панели администратора!', reply_markup=admin_kb)
    else:
        await message.answer('У вас нет доступа к панели администратора!')

@admin_router.message(F.text=='Создать встречу')
async def make_meet(message: types.Message, state: FSMContext):
    await message.answer('Выберите месяц', reply_markup=await calendar_month())
    await state.set_state(AddMeet.month)

@admin_router.callback_query(AddMeet.month)
async def calendaric_month(callback: CallbackQuery, state: FSMContext):
    month = callback.data
    await state.update_data(month=month)
    await callback.message.edit_text('Выберите дату', reply_markup=await calendar_day(month))
    await state.set_state(AddMeet.day)

@admin_router.callback_query(AddMeet.day)
async def calendaric_day(callback: CallbackQuery, state: FSMContext):
    day = callback.data
    if day == 'назад':
        await callback.message.edit_text('Выберите месяц', reply_markup=await calendar_month())
        await state.set_state(AddMeet.month)
        return
        
    await state.update_data(day=day)
    meet = await state.get_data()
    month = meet['month']
    day = meet['day']
    if int(day) < 10:
        day = '0' + day
    months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
              'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    month = str(months.index(month) + 1)
    if int(month) < 10:
        month = '0' + month
    date = day + '.' + month
    await callback.message.edit_text('Выберите время', reply_markup=await calendar_time(date))
    await state.set_state(AddMeet.time)

time_list = set()

@admin_router.message(F.text=='Расписание встреч')
async def show_schedule(message: types.Message):
    today = date.today().strftime('%d.%m.%Y')
    meetings = db.get_meetings_by_date(today)
    
    if not meetings:
        await message.answer('Встреч пока нет!', reply_markup=admin_kb)
        return
        
    message_to_answer = 'Расписание встреч на сегодня:\n\n'
    for meeting in meetings:
        week_day = datetime.strptime(meeting['date'], '%d.%m.%Y').weekday()
        weekdays_dict = {
            0: 'понедельник', 1: 'вторник', 2: 'среда', 3: 'четверг',
            4: 'пятница', 5: 'суббота', 6: 'воскресенье'
        }
        
        message_to_answer += (
            f'Встреча №{meeting["id"]}\n'
            f'Дата: {meeting["date"]}\n'
            f'День недели: {weekdays_dict[week_day]}\n'
            f'Время: {meeting["time"]}\n'
            f'Статус: {meeting["status"]}\n'
            f'Тренер: {meeting["client_nickname"] or "Не назначен"}\n\n'
        )
    
    await message.answer(message_to_answer, reply_markup=admin_kb)

@admin_router.callback_query(AddMeet.time)
async def select_name(callback: CallbackQuery, state: FSMContext):
    global time_list
    times = callback.data
    meet = await state.get_data()
    day = meet['day']
    month = meet['month']
    
    months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
              'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    
    if times == 'назад':
        time_list = set()
        await callback.message.edit_text('Выберите дату', reply_markup=await calendar_day(month))
        await state.set_state(AddMeet.day)
        return
        
    if callback.data == 'создать встречи':
        if len(time_list) == 0:
            await callback.answer('Вы не выбрали время!')
            await state.set_state(AddMeet.time)
        else:
            current_year = datetime.now().year
            
            meetings_created = []
            
            for time in time_list:
                formatted_day = f'{int(day):02d}'
                month_num = months.index(month) + 1
                formatted_month = f'{month_num:02d}'
                
                date_str = f'{formatted_day}.{formatted_month}.{current_year}'
                
                meeting_id = db.create_meeting(date_str, time)
                meetings_created.append(f'{date_str} на {time}')
            
            if meetings_created:
                 await callback.message.answer(f'Отлично, вы создали встречу на: {', '.join(meetings_created)}', reply_markup=admin_kb)
            else:
                 await callback.message.answer('Не удалось создать встречи.', reply_markup=admin_kb)
                 
            await state.clear()
            time_list = set()
    else:
        if callback.data in time_list:
            time_list.discard(callback.data)
            meet_date = f'{int(day):02d}.{months.index(month)+1:02d}'
            await callback.message.edit_text('Выберите время', reply_markup=await calendar_time(meet_date, dobavlen=time_list))
            await state.set_state(AddMeet.time)
        else:
            time_list.add(callback.data)
            meet_date = f'{int(day):02d}.{months.index(month)+1:02d}'
            await callback.message.edit_text('Выберите время', reply_markup=await calendar_time(meet_date, dobavlen=time_list))
            await state.set_state(AddMeet.time)

@admin_router.message(F.text=='Встречи на сегодня')
async def raspisanie_na_segodnya(message: types.Message, bot: Bot):
    today = date.today().strftime('%d.%m.%Y')
    meetings = db.get_meetings_by_date(today)

    if not meetings:
        # Если вообще нет встреч на сегодня
        await message.answer('На сегодня никто не записан!', reply_markup=admin_kb)
        return

    message_to_answer = ''
    booked_meetings_count = 0
    for meeting in meetings:
        # Включаем в сообщение только встречи с назначенным клиентом
        if meeting['client_nickname']:
            booked_meetings_count += 1
            week_day = datetime.strptime(meeting['date'], '%d.%m.%Y').weekday()
            weekdays_dict = {
                0: 'понедельник', 1: 'вторник', 2: 'среда', 3: 'четверг',
                4: 'пятница', 5: 'суббота', 6: 'воскресенье'
            }

            message_to_answer += (
                f'Встреча №{meeting["id"]}\n'
                f'Дата: {meeting["date"]}\n'
                f'День недели: {weekdays_dict[week_day]}\n'
                f'Время: {meeting["time"]}\n'
                f'Тренер: {meeting["client_nickname"]}\n\n' # Здесь уже точно есть никнейм
            )

    if booked_meetings_count == 0:
        # Если встречи на сегодня есть, но ни одна не занята
        await message.answer('На сегодня никто не записан!', reply_markup=admin_kb)
    else:
        # Если есть хотя бы одна занятая встреча
        await message.answer(message_to_answer, reply_markup=admin_kb)

@admin_router.message(F.text=='Все встречи')
async def raspisanie(message: types.Message):
    meetings = db.get_all_meetings()
    
    if not meetings:
        await message.answer('Встреч пока нет!')
        return
        
    message_to_answer = ''
    for meeting in meetings:
        week_day = datetime.strptime(meeting['date'], '%d.%m.%Y').weekday()
        weekdays_dict = {
            0: 'понедельник', 1: 'вторник', 2: 'среда', 3: 'четверг',
            4: 'пятница', 5: 'суббота', 6: 'воскресенье'
        }
        
        message_to_answer += (
            f'Встреча №{meeting["id"]}\n'
            f'Дата: {meeting["date"]}\n'
            f'День недели: {weekdays_dict[week_day]}\n'
            f'Время: {meeting["time"]}\n'
            f'Тренер: {meeting["client_nickname"] or "Не назначен"}\n\n'
        )
    
    await message.answer(message_to_answer, reply_markup=admin_kb)

@admin_router.message(F.text=='Отменить/перенести')
async def much_meet(message: types.Message, state: FSMContext):
    meetings = db.get_all_meetings()
    
    if not meetings:
        await message.answer('Встреч пока нет!', reply_markup=admin_kb)
        return
        
    message_to_answer = 'Выберите номер встречи:\n\n'
    for meeting in meetings:
        message_to_answer += (
            f'Встреча №{meeting["id"]}\n'
            f'Дата: {meeting["date"]}\n'
            f'Время: {meeting["time"]}\n'
            f'Статус: {meeting["status"]}\n'
            f'Тренер: {meeting["client_nickname"] or "Не назначен"}\n\n'
        )
    
    await message.answer('Выберите номер встречи')
    await message.answer(message_to_answer, reply_markup=ReplyKeyboardRemove())
    await state.set_state(ChangeMeet.vvod)

@admin_router.message(ChangeMeet.vvod, F.text)
async def change_meet(message: types.Message, state: FSMContext):
    try:
        meeting_id = int(message.text)
    except ValueError:
        await message.answer('Пожалуйста, введите числовой номер встречи.', reply_markup=admin_kb)
        await state.clear()
        return

    meeting = db.get_meeting(meeting_id)
    if not meeting:
        await message.answer('Встречи с таким номером не существует.', reply_markup=admin_kb)
        await state.clear()
        return

    global chose
    chose = message.text
    await message.answer('Что вы хотите с ней сделать?', reply_markup=change_kb)
    await state.clear()

@admin_router.message(F.text=='Удалить встречу')
async def delete_meet(message: types.Message, bot: Bot):
    global chose
    if not chose:
        await message.answer('Пожалуйста, сначала выберите встречу для удаления.', reply_markup=admin_kb)
        return

    try:
        meeting_id = int(chose)
    except ValueError:
        await message.answer('Неверный номер встречи.', reply_markup=admin_kb)
        return

    meeting = db.get_meeting(meeting_id)
    if meeting:
        user_id_to_notify = None
        if meeting.get('client_id'):
            user_id_to_notify = db.get_user_id_by_internal_id(meeting['client_id'])

        db.delete_meeting(meeting_id)

        if user_id_to_notify:
            await bot.send_message(user_id_to_notify, f'Встреча №{meeting_id}, на которую вы записывались, была удалена администратором.')

        await message.answer(f'Встреча №{meeting_id} успешно удалена!', reply_markup=admin_kb)

    else:
        await message.answer(f'Встречи №{meeting_id} нет!', reply_markup=admin_kb)
    
    chose = None

@admin_router.message(F.text=='Удалить все встречи')
async def delete_all_meetings(message: types.Message, bot: Bot):
    if message.from_user.id in ADMINS:
        deleted_count = db.cleanup_old_meetings()
        await message.answer(f'Удалено {deleted_count} прошедших встреч')
        await bot.send_message(ADMIN_ID, f'Удалено {deleted_count} прошедших встреч')
    else:
        await message.answer('У вас нет доступа к этой команде!')

@admin_router.message(F.text=='Изменить время')
async def change_time(message: types.Message, state: FSMContext):
    meeting = db.get_meeting(int(chose))
    if meeting:
        await state.set_state(ChangeMeet.time)
        await message.answer('Введите новое время', reply_markup=await calendar_time(str(date.today())[5:].replace('-', '.')))
    else:
        await message.answer('Такой встречи нет')

@admin_router.message(F.text=='Изменить дату')
async def change_date(message: types.Message, state: FSMContext):
    meeting = db.get_meeting(int(chose))
    if meeting:
        await state.set_state(ChangeMeet.month)
        await message.answer('Введите новую дату', reply_markup=await calendar_month())
    else:
        await message.answer('Такой встречи нет')

@admin_router.callback_query(ChangeMeet.time)
async def change_time1(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.update_data(time=callback.data)
    await callback.message.delete()
    meet = await state.get_data()
    time = meet['time']
    
    meeting = db.get_meeting(int(chose))
    if meeting:
        db.update_meeting_time(int(chose), time)
        await callback.message.answer(f'Время успешно изменено на {time}', reply_markup=admin_kb)
        
        if meeting.get('client_id'):
            user_id = db.get_user_id_by_internal_id(meeting['client_id'])
            if user_id:
                await bot.send_message(user_id, f'Время встречи, на которую вы записывались изменилось на {time}')
    
    await state.clear()

@admin_router.callback_query(ChangeMeet.month)
async def change_name1(callback: CallbackQuery, state: FSMContext):
    await state.update_data(month=callback.data)
    await callback.message.edit_text('Выберите новую дату', reply_markup=await calendar_day(callback.data))
    await state.set_state(ChangeMeet.day)

@admin_router.callback_query(ChangeMeet.day)
async def change_date2(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.update_data(day=callback.data)
    await callback.message.delete()
    meet = await state.get_data()
    month = meet['month']
    day = meet['day']
    
    if int(day) < 10:
        day = '0' + day
    months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
              'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    month = str(months.index(month) + 1)
    if int(month) < 10:
        month = '0' + month
    date = day + '.' + month
    
    meeting = db.get_meeting(int(chose))
    if meeting:
        db.update_meeting_date(int(chose), date)
        await callback.message.answer(f'Дата успешно изменена на {date}', reply_markup=admin_kb)
        
        if meeting.get('client_id'):
            user_id = db.get_user_id_by_internal_id(meeting['client_id'])
            if user_id:
                await bot.send_message(user_id, f'Дата встречи, на которую вы записывались изменилась на {date}')
    
    await state.clear()

congratulations = [
    'Поздравляю с днём старения, ну то есть с днём рождения 🥳 🎂',
    'С днем рожденья, с праздником, в который мир увидел такое чудо в перьях, как ты.',
    'Поздравляю с днем рождения и хочу пожелать счастливой лыбы до ушей и неугомонного шила в твоей попе, а ещё — взрывных идей веселья и крутой фантазии, которая позволит оставаться пофигистом для проблем и оптимистом по жизни!',
    'Жизнь коротка! Нарушай правила!, Но не на работе С днём рождения 🤗🎂!!!!'
]

@admin_router.message(F.text=='чек др')
async def check_dr_7(bot: Bot):
    # Проверяем дни рождения на следующую неделю
    upcoming = db.get_upcoming_birthdays(7)
    for birthday in upcoming:
        if birthday['days_until'] > 0:
            await bot.send_message(
                676770835,
                f'У {birthday["nickname"]} день рождение через {birthday["days_until"]} дней! '
                f'Ему кстати исполняется {birthday["age"]} лет'
            )
    
    # Проверяем дни рождения сегодня
    today_birthdays = [b for b in upcoming if b['days_until'] == 0]
    for birthday in today_birthdays:
        await bot.send_message(
            676770835,
            f'У {birthday["nickname"]} сегодня день рождение! Не забудь поздравить!'
        )
        await bot.send_message(birthday['user_id'], choice(congratulations))

@admin_router.message(F.text=='дел мет')
async def cleanup_meetings(bot: Bot):
    deleted_count = db.cleanup_old_meetings()
    if deleted_count > 0:
        await bot.send_message(676770835, f'Удалено {deleted_count} прошедших встреч')

@admin_router.message(F.text=='уведомление илье')
async def yved_ikya_o_vstreche(bot: Bot):
    today = date.today().strftime('%d.%m.%Y')
    meetings = db.get_meetings_by_date(today)
    
    if not meetings:
        await bot.send_message(676770835, 'На сегодня встреч нет')
        return
    
    message_to_answer = ''
    for meeting in meetings:
        if meeting['client_nickname']:
            week_day = datetime.strptime(meeting['date'], '%d.%m.%Y').weekday()
            weekdays_dict = {
                0: 'понедельник', 1: 'вторник', 2: 'среда', 3: 'четверг',
                4: 'пятница', 5: 'суббота', 6: 'воскресенье'
            }
            
            message_to_answer += (
                f'Встреча №{meeting["id"]}\n'
                f'Дата: {meeting["date"]}\n'
                f'День недели: {weekdays_dict[week_day]}\n'
                f'Время: {meeting["time"]}\n'
                f'Тренер: {meeting["client_nickname"]}\n\n'
            )
    
    if message_to_answer:
        await bot.send_message(676770835, message_to_answer)
        await bot.send_message(676770835, 'Это все встречи, запланированные на сегодня')
    else:
        await bot.send_message(676770835, 'На сегодня никто не записан')

# Функция для ежедневной проверки (без callback и state)
async def check_daily_meetings(bot: Bot):
    today = date.today().strftime('%d.%m.%Y')
    meetings = db.get_meetings_by_date(today)
    
    if not meetings:
        await bot.send_message(676770835, 'На сегодня встреч нет')
        return
    
    message_to_answer = ''
    for meeting in meetings:
        if meeting['client_nickname']:
            week_day = datetime.strptime(meeting['date'], '%d.%m.%Y').weekday()
            weekdays_dict = {
                0: 'понедельник', 1: 'вторник', 2: 'среда', 3: 'четверг',
                4: 'пятница', 5: 'суббота', 6: 'воскресенье'
            }
            
            message_to_answer += (
                f'Встреча №{meeting["id"]}\n'
                f'Дата: {meeting["date"]}\n'
                f'День недели: {weekdays_dict[week_day]}\n'
                f'Время: {meeting["time"]}\n'
                f'Тренер: {meeting["client_nickname"]}\n\n'
            )
    
    if message_to_answer:
        await bot.send_message(676770835, message_to_answer)
        await bot.send_message(676770835, 'Это все встречи, запланированные на сегодня')
    else:
        await bot.send_message(676770835, 'На сегодня никто не записан')

# Функция для автоматического удаления встреч (без message)
async def cleanup_old_meetings(bot: Bot):
    deleted_count = db.cleanup_old_meetings()
    if deleted_count > 0:
        await bot.send_message(676770835, f'Удалено {deleted_count} прошедших встреч')

@admin_router.message(F.text=='Удалить прошедшие встречи')
async def delete_meet(message: types.Message, bot: Bot):
    if message.from_user.id in ADMINS:
        deleted_count = db.cleanup_old_meetings()
        await message.answer(f'Удалено {deleted_count} прошедших встреч')
        await bot.send_message(ADMIN_ID, f'Удалено {deleted_count} прошедших встреч')
    else:
        await message.answer('У вас нет доступа к этой команде!')

@admin_router.message(F.text=='Проверить встречи на сегодня')
async def check_meetings(message: types.Message, bot: Bot):
    if message.from_user.id in ADMINS:
        today = datetime.now().strftime('%d.%m.%Y')
        meetings = db.get_meetings_by_date(today)
        
        if not meetings:
            await message.answer('На сегодня встреч нет')
            await bot.send_message(ADMIN_ID, 'На сегодня встреч нет')
            return
            
        message_to_answer = 'Встречи на сегодня:\n\n'
        for meeting in meetings:
            if meeting['client_nickname']:
                message_to_answer += (
                    f'Встреча №{meeting["id"]}\n'
                    f'Время: {meeting["time"]}\n'
                    f'Клиент: {meeting["client_nickname"]}\n\n'
                )
            else:
                message_to_answer += (
                    f'Встреча №{meeting["id"]}\n'
                    f'Время: {meeting["time"]}\n'
                    f'Статус: {meeting["status"]}\n\n'
                )
                
        await message.answer(message_to_answer)
        await bot.send_message(ADMIN_ID, message_to_answer)
        await bot.send_message(ADMIN_ID, 'Это все встречи, запланированные на сегодня')
    else:
        await message.answer('У вас нет доступа к этой команде!')

@admin_router.message(F.text=='Проверить записи на сегодня')
async def check_bookings(message: types.Message, bot: Bot):
    if message.from_user.id in ADMINS:
        today = datetime.now().strftime('%d.%m.%Y')
        meetings = db.get_meetings_by_date(today)
        
        if not meetings:
            await message.answer('На сегодня встреч нет')
            await bot.send_message(ADMIN_ID, 'На сегодня встреч нет')
            return
            
        booked_meetings = [m for m in meetings if m['client_nickname']]
        
        if not booked_meetings:
            await message.answer('На сегодня никто не записан')
            await bot.send_message(ADMIN_ID, 'На сегодня никто не записан')
            return
            
        message_to_answer = 'Записи на сегодня:\n\n'
        for meeting in booked_meetings:
            message_to_answer += (
                f'Встреча №{meeting["id"]}\n'
                f'Время: {meeting["time"]}\n'
                f'Клиент: {meeting["client_nickname"]}\n\n'
            )
                
        await message.answer(message_to_answer)
        await bot.send_message(ADMIN_ID, message_to_answer)
        await bot.send_message(ADMIN_ID, 'Это все встречи, запланированные на сегодня')
    else:
        await message.answer('У вас нет доступа к этой команде!')





