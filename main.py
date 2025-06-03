import os
import asyncio
from dotenv import find_dotenv, load_dotenv
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from handlers.admin_router import check_dr_7, yved_ikya_o_vstreche, check_daily_meetings, cleanup_old_meetings
from handlers.admin_router import admin_router
from handlers.user_router import user_router

load_dotenv(find_dotenv())

TOKEN = os.getenv('TOKEN')

if not TOKEN:
    # Можно добавить здесь более информативное сообщение об ошибке или логирование
    pass # Или оставить pass, если обработка ошибок будет в другом месте

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()

dp.include_router(admin_router)
dp.include_router(user_router)


async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(check_daily_meetings, trigger='cron', hour=18, minute=00, kwargs={'bot':bot})
    scheduler.add_job(check_dr_7, trigger='cron', hour=9, minute=0, kwargs={'bot': bot})
    scheduler.add_job(cleanup_old_meetings, trigger='cron', hour=0, minute=0, kwargs={'bot': bot})
    scheduler.add_job(yved_ikya_o_vstreche, trigger='cron', hour=9, minute=00, kwargs={'bot': bot})
    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

asyncio.run(main())



