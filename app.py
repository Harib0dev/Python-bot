# EndSoft - https://t.me/end_soft
import asyncio
import traceback
from colorama import Fore, Style, init
from loader import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
from utils.paginator import Paginator


async def on_startup(dp):
    from utils.set_bot_commands import set_default_commands
    await set_default_commands(dp)
    bot_info = await dp.bot.get_me()
    print(f"{Style.BRIGHT}{Fore.CYAN}https://t.me/{bot_info.username} запущен успешно!", Style.RESET_ALL)
    Paginator().importer()
    await lolz.get_me()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(func=send_logs, trigger="cron", hour=0, )
    scheduler.start()
    asyncio.create_task(get_payments_from_lolz())


async def get_payments_from_lolz():
    while True:
        await asyncio.sleep(5)
        await lolz.get_payments()


async def send_logs():
    try:
        date = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%d-%m-%Y")
        with open(f'logs/{date}.log', "rb") as reader:
            await bot.send_document(chat_id=CHANNEL_ID, caption=f"<b>Логи за {date.replace('-', ' ')}</b>", document=reader)
    except Exception:
        print(traceback.format_exc())


if __name__ == '__main__':
    from aiogram import executor
    from handlers import dp
    from utils.throttling import ThrottlingMiddleware
    try:
        dp.middleware.setup(ThrottlingMiddleware())
        executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
    finally:
        Paginator().exporter()
        
        # EndSoft - https://t.me/end_soft
