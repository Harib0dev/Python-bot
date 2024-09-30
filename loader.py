# EndSoft - https://t.me/end_soft

import traceback
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from data.config import *
import mysql.connector
from pyqiwip2p import QiwiP2P
from aiogram.types import ParseMode, ReplyKeyboardRemove, ReplyKeyboardMarkup, \
    KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions, BotCommand
from aiogram.dispatcher.filters.state import State, StatesGroup
from loguru import logger
import datetime
from api.lolz import LolzTeam


bot = Bot(BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot=bot, storage=MemoryStorage())

conn = mysql.connector.connect(user='root', password='ПАРОЛЬ ОТ ROOT',
                              host='127.0.0.1',
                              database='НАЗВАНИЕ БАЗЫ')

cur = conn.cursor()

p2p = QiwiP2P(auth_key=QIWI_KEY)


lolz_session = aiohttp.ClientSession()
try:
    lolz = LolzTeam(token=LOLZ_TOKEN, session=lolz_session)
except Exception:
    print(traceback.format_exc())


MAIN_KEYBOARD = ReplyKeyboardMarkup(resize_keyboard=True)
MAIN_KEYBOARD.add(KeyboardButton(text="💲 Купить"))
MAIN_KEYBOARD.add(KeyboardButton(text="ℹ Личный кабинет"), KeyboardButton(text="💬 Информация"))

ADMIN_KEYBOARD = ReplyKeyboardMarkup(resize_keyboard=True)
ADMIN_KEYBOARD.add(KeyboardButton(text="Управление юрентом"), KeyboardButton(text="Управление пополнениями"))
ADMIN_KEYBOARD.add(KeyboardButton(text="Рассылка"), KeyboardButton(text="Невалид"))
ADMIN_KEYBOARD.add(KeyboardButton(text="Управление пользователями"), KeyboardButton(text="Управление промокодами"))


class Form(StatesGroup):
    mailing_msg = State()
    name_of_promo = State()
    number_of_uses = State()
    price_of_promo = State()
    count_promocodes = State()
    info_promocode = State()
    get_promo_for_activate = State()
    get_user_id = State()
    get_amount_qiwi = State()
    get_amount_lolz = State()
    get_amount_payok = State()
    get_issue_money = State()
    get_fetch_money = State()
    get_token = State()
    account_number = State()
    payment_data = State()
    list_of_promocodes = State()
    get_count_account_to_create = State()
    get_promocodes = State()
    get_price = State()
    get_description = State()
    cancel_msgID = State()
    get_number_card = State()
    get_exp_card = State()
    get_cvv_card = State()
    get_scooter = State()
    linked_account = State()


logger.add(f"logs/{datetime.datetime.today().strftime('%d-%m-%Y')}.log",
           format="{time:DD-MMM-YYYY HH:mm:ss} | {level:^25} | {message}", enqueue=True, rotation="00:00")

logger.level("JOIN", no=60, color="<red>")
logger.level("SPAM", no=60, color="<red>")

logger.level("BUY-ACCOUNT", no=60, color="<blue>")
logger.level("START-UR-RIDE", no=60, color="<blue>")
logger.level("END-UR-RIDE", no=60, color="<blue>")
logger.level("PAUSE-UR-RIDE", no=60, color="<blue>")
logger.level("RESUME-UR-RIDE", no=60, color="<blue>")

logger.level("LINK-CARD", no=60, color="<yellow>") #    ДОДЕЛАТЬ
logger.level("UNLINK-CARD", no=60, color="<yellow>")

logger.level("BALANCE-REPLENISHMENT", no=60, color="<green>")

logger.level("ACTIVATE-PROMOCODE", no=60, color="<magenta>")

# EndSoft - https://t.me/end_soft