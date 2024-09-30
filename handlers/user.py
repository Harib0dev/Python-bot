# EndSoft - https://t.me/end_soft
import asyncio
import datetime
import json
import os
import re
import time
import traceback
import uuid
from collections import Counter
from functools import reduce
from random import choice, randint
from pprint import pprint   # For easy viewing
import cv2
from pyzbar import pyzbar
import aiohttp
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import ParseMode, ReplyKeyboardRemove, ReplyKeyboardMarkup, \
    KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions, BotCommand
from aiogram.types.web_app_info import WebAppInfo
from aiogram.utils import executor
from aiogram.utils.exceptions import Throttled
from loader import *
from numpy import arange
from utils.is_status import *
from utils.throttling import rate_limit
from api.urent import UrentApi
from uuid import uuid4
from utils.paginator import paginator, Paginator


@dp.message_handler(commands=['start'])
@rate_limit(limit=3, key="start")
# @dp.throttled(anti_flood, rate=3)
@is_baned
async def start(message, **kwargs):
    await bot.send_message(chat_id=message.chat.id, text=f'<b>Добро пожаловать, {message.from_user.first_name}\n'
                                                         f'<a href="https://t.me/end_soft">Подпишитесь на канал</a>\n'
                                                         f'Спасибо, что решили воспользоваться нашим сервисом</b>',
                           reply_markup=MAIN_KEYBOARD, disable_web_page_preview=True)
    try:

        cur.execute("SELECT user_id FROM users_info WHERE user_id=%s", (message.chat.id, ))
        if cur.fetchall() == []:
            cur.execute('SELECT * FROM users_info WHERE user_id=%s', (''.join(message.text.split(' ')[1:]), ))
            refferal = cur.fetchall()
            cur.execute("INSERT INTO users_info (user_id, balance, total_balance, number_purchases, total_sum_purchases, ban_status, referral, earning_referrals) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (message.chat.id, 0, 0, 0, 0, 0, int(f"{0 if refferal == [] else ''.join(message.text.split(' ')[1:])}"), 0))
            conn.commit()
            if refferal != []:
                try:
                    await bot.send_message(chat_id=''.join(message.text.split(' ')[1:]), text="<b>У вас появился новый реферал!</b>")
                except Exception:
                    pass
            await bot.send_message(chat_id=CHANNEL_ID, text=f"<b>👤 Присоединился новый пользователь @{message.from_user.username}</b>")
            logger.log("JOIN", f"{message.chat.id}")
    except Exception:
        print(traceback.format_exc())


@dp.message_handler(lambda message: message.text == "💲 Купить")
@rate_limit(limit=3, key="buy")
# @dp.throttled(anti_flood, rate=3)
@is_baned
async def buy_panel(message, **kwargs):
    BUY_KEYBOARD = InlineKeyboardMarkup(row_width=1)
    BUY_KEYBOARD.add(InlineKeyboardButton(text="🟣 Юрент", callback_data="category-urent"))
    await bot.send_message(chat_id=message.chat.id, text=f"<b>🛍 Выберите категорию:</b>", reply_markup=BUY_KEYBOARD)


@dp.callback_query_handler(lambda call: call.data == "back-to-buy-panel")
async def back_to_buy_panel(call):
    BUY_KEYBOARD = InlineKeyboardMarkup(row_width=1)
    BUY_KEYBOARD.add(InlineKeyboardButton(text="🟣 Юрент", callback_data="category-urent"))
    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                text=f"<b>🛍 Выберите категорию:</b>", reply_markup=BUY_KEYBOARD)


@dp.callback_query_handler(lambda call: call.data == "category-urent")
async def category_urent(call, state: FSMContext):
    cur.execute("SELECT * FROM ur_accounts WHERE user_id=%s", (0,))
    list_of_accounts = cur.fetchall()
    dict_of_prices = Counter([(item[2], item[4]) for item in list_of_accounts])
    BUY_KEYBOARD = InlineKeyboardMarkup(row_width=1)
    BUY_KEYBOARD.add(*[InlineKeyboardButton(text=f'{str(j[0]).rjust(3)} ₽ | {str(j[1]).rjust(3)} | {dict_of_prices[j] if int(dict_of_prices[j]) <= 99 else "99+"} шт.',
                                            callback_data=f"buy-account-ask_{j[0]}") for j in dict_of_prices.keys()])
    BUY_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-buy-panel"))
    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                text=f"<b>Выберите нужный вам аккаунт:</b>", reply_markup=BUY_KEYBOARD)


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "buy-account-ask")
async def buy_account_ask(call, state: FSMContext):
    try:
        ASK_KEYBOARD = InlineKeyboardMarkup()
        ASK_KEYBOARD.add(InlineKeyboardButton(text="✅ Подтвердить покупку", callback_data=f"buy-process_{call.data.split('_')[1]}"))
        ASK_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-buy-panel"))
        cur.execute("SELECT * FROM ur_accounts WHERE user_id=%s and price=%s", (0, call.data.split("_")[1]))
        account_info = cur.fetchall()
        link = "https://telegra.ph/Instrukciya-po-ispolzovaniyu-YUrent-cherez-Cheap-Shop-04-02"
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text=f"<b>🛍  Товар:</b> {account_info[0][4]}\n"
                                         f"<b>🏷 Описание: Аккаунты Urent, 1б=1руб.\n"
                                         f"Оплата баллами 100%\n\n"
                                         f"✅ Гарантия 24 часа\n"
                                         f"📒 Тарифы: Поминутный, На час, До полного разряда\n\n"
                                         f"<a href='{link}'>Инструкцию по использованию (БОТ)</a>\n\n"
                                         f"💼 В наличие:</b> {len(account_info)}\n"
                                         f"<b>💵 Цена</b>: {account_info[0][2]}", reply_markup=ASK_KEYBOARD, disable_web_page_preview=True)
    except Exception:
        await bot.send_message(chat_id=call.message.chat.id, text="<b>Что то пошло не так... Возможно нужный вам товар уже куплен</b>")


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "buy-process")
async def buy_account_process(call):
    try:
        cur.execute("SELECT balance FROM users_info WHERE user_id=%s", (call.message.chat.id,))
        if cur.fetchall()[0][0] >= int(call.data.split("_")[1]):
            cur.execute("SELECT * FROM ur_accounts WHERE user_id=%s and price=%s", (0, call.data.split("_")[1]))
            account_info = choice(cur.fetchall())
            GET_ACCOUNT = InlineKeyboardMarkup()
            GET_ACCOUNT.add(InlineKeyboardButton(text="Перейти к аккаунту", callback_data=f"select-account_{account_info[0]}"))
            await bot.edit_message_text(chat_id=call.message.chat.id, text=f"<b>💸 Аккаунт был успешно куплен:</b>\n"
                                                                           f"<b>📞 Номер:</b> <code>{account_info[0]}</code>\n\n"
                                                                           f"<b>Перейдите по кнопке ниже или <i>Личный кабинет -> Мои аккаунты</i>, для управление аккаунтом.</b>\n\n"
                                                                           f"<b>Спасибо что используете наш сервис!</b>", message_id=call.message.message_id, reply_markup=GET_ACCOUNT)
            cur.execute("UPDATE users_info SET balance=balance-%s, number_purchases=number_purchases+1, "
                        "total_sum_purchases=total_sum_purchases+%s WHERE user_id=%s",
                        (call.data.split("_")[1], call.data.split("_")[1], call.message.chat.id))
            cur.execute("UPDATE ur_accounts SET user_id=%s, get_datetime=%s WHERE phone_number=%s", (call.message.chat.id, datetime.datetime.now(), account_info[0]))
            conn.commit()
            logger.log("BUY-ACCOUNT", f"{call.message.chat.id} | {account_info[0]} | {call.data.split('_')[1]}")
            await bot.send_message(chat_id=CHANNEL_ID,
                                   text=f"<b>💸 ID: <code>{call.message.chat.id}</code>\n"
                                        f"💸 URERNAME: <code>@{call.message.chat.username}</code>\n"
                                        f"💸 Был куплен аккаунт Юрент за {call.data.split('_')[1]} рублей.</b>")
        else:
            await call.answer('⛔ Не достаточно средств на аккаунте!', show_alert=True)
    except Exception:
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        await bot.send_message(chat_id=call.message.chat.id,
                               text="<b>Что то пошло не так, возможно нужный товар закончился</b>")
        print(traceback.format_exc())


@dp.message_handler(lambda message: message.text == "ℹ Личный кабинет")
@rate_limit(limit=3, key="personal_account")
# @dp.throttled(anti_flood, rate=3)
@is_baned
async def personal_account(message, req=False, **kwargs):
    cur.execute("SELECT * FROM users_info WHERE user_id=%s", (message.chat.id,))
    user_info = cur.fetchall()[0]

    PERSONAL_ACCOUNT_KEYBOARD = InlineKeyboardMarkup()
    PERSONAL_ACCOUNT_KEYBOARD.add(InlineKeyboardButton(text="Мои карты", callback_data="my-cards"),
                                  InlineKeyboardButton(text="Мои аккаунты", callback_data="my-accounts"))
    PERSONAL_ACCOUNT_KEYBOARD.add(InlineKeyboardButton(text="Пополнить баланс", callback_data="replenish-balance"))
    PERSONAL_ACCOUNT_KEYBOARD.add(InlineKeyboardButton(text="Реферальная система", callback_data="referral-system"))
    PERSONAL_ACCOUNT_KEYBOARD.add(InlineKeyboardButton(text="Активировать промокод", callback_data="activate-promo"))

    text = f"<b>👤 Пользователь:</b> @{message.chat.username}\n" \
           f"<b>🪪 ID:</b> <code>{message.chat.id}</code>\n" \
           f"<b>💰 Баланс:</b> <code>{user_info[1]} ₽</code> \n" \
           f"<b>📊 Количество покупок:</b> <code>{user_info[3]}</code>\n" \
           f"<b>💲 Общая сумма покупок:</b> <code>{user_info[4]} ₽</code>\n" \
           f"<b>💸 Общая сумма пополнений:</b> <code>{user_info[2]} ₽</code>\n"
    if not req:
        await bot.send_message(chat_id=message.chat.id, text=text, reply_markup=PERSONAL_ACCOUNT_KEYBOARD)
    else:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text, reply_markup=PERSONAL_ACCOUNT_KEYBOARD)


@dp.callback_query_handler(lambda call: call.data == "my-cards" or call.data == "back-to-my-cards")
async def my_cards(call):
    cur.execute("SELECT * FROM cards WHERE user_id=%s", (call.message.chat.id,))
    cards_info = cur.fetchall()
    if not cards_info:
        CARD_KEYBOARD = InlineKeyboardMarkup()
        CARD_KEYBOARD.add(InlineKeyboardButton(text="Добавить карту", callback_data="add-card"))
        CARD_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-personal-account"))
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="<b>На данный момент у вас нет привязанных карт.</b>",
                                    reply_markup=CARD_KEYBOARD)
    else:
        CARD_KEYBOARD = InlineKeyboardMarkup(row_width=2)
        CARD_KEYBOARD.add(*sum([[InlineKeyboardButton(text=item[1], callback_data=f"select-card_{item[1]}"),
                                 InlineKeyboardButton(text="Удалить", callback_data=f"delete-card_{item[1]}")] for item in cards_info], []))
        CARD_KEYBOARD.add(InlineKeyboardButton(text="Добавить карту", callback_data="add-card"))
        CARD_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-personal-account"))
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="<b>Ваши карты:</b>", reply_markup=CARD_KEYBOARD)


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "delete-card")
async def delete_card(call):
    cur.execute("DELETE FROM cards WHERE user_id=%s and card_number=%s", (call.message.chat.id, call.data.split("_")[1], ))
    conn.commit()
    cur.execute("SELECT * FROM cards WHERE user_id=%s", (call.message.chat.id,))
    cards_info = cur.fetchall()
    CARD_KEYBOARD = InlineKeyboardMarkup(row_width=2)
    CARD_KEYBOARD.add(*sum([[InlineKeyboardButton(text=item[1], callback_data=f"select-card_{item[1]}"),
                             InlineKeyboardButton(text="Удалить", callback_data=f"delete-card_{item[1]}")] for item in
                            cards_info], []))
    CARD_KEYBOARD.add(InlineKeyboardButton(text="Добавить карту", callback_data="add-card"))
    CARD_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-personal-account"))

    await call.answer("❗ Успешно удалено.", show_alert=False)
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=CARD_KEYBOARD)


@dp.callback_query_handler(lambda call: call.data == "add-card")
async def add_card_number_get(call, state: FSMContext):
    BACK_KEYBOARD = InlineKeyboardMarkup()
    BACK_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-personal-account"))
    await Form.get_number_card.set()
    msg = await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="<b>Введите номер карты:</b>", reply_markup=BACK_KEYBOARD)
    await state.update_data(cancel_msgID=msg.message_id)


@dp.message_handler(state=Form.get_number_card)
async def add_card_exp_get(message, state: FSMContext):
    async with state.proxy() as cancel:
        await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=cancel["cancel_msgID"],
                                            reply_markup=InlineKeyboardMarkup([[]]))
    BACK_KEYBOARD = InlineKeyboardMarkup()
    BACK_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-personal-account"))
    try:
        cur.execute("SELECT * FROM cards WHERE user_id=%s and card_number=%s", (message.chat.id, message.text))
        cards = cur.fetchall()
        if len(cards) != 0:
            msg = await bot.send_message(chat_id=message.chat.id,
                                         text="<b>Эта карта уже добавлена, попробуйте другую.</b>",
                                         reply_markup=BACK_KEYBOARD)
            await state.update_data(cancel_msgID=msg.message_id)
            return 0

        LOOKUP = (0, 2, 4, 6, 8, 1, 3, 5, 7, 9)
        code = reduce(str.__add__, filter(str.isdigit, message.text))
        evens = sum(int(i) for i in code[-1::-2])
        odds = sum(LOOKUP[int(i)] for i in code[-2::-2])
        if (evens + odds) % 10 == 0:
            await state.update_data(get_number_card="".join(symbol for symbol in message.text if symbol.isdecimal()))
            await Form.get_exp_card.set()
            msg = await bot.send_message(chat_id=message.chat.id,
                                         text="<b>Введите срок действия карты в формате <code>мм/гг</code></b>",
                                         reply_markup=BACK_KEYBOARD)
            await state.update_data(cancel_msgID=msg.message_id)
        else:
            raise Exception
    except Exception:
        msg = await bot.send_message(chat_id=message.chat.id,
                                     text="<b>Это не похоже на номер карты попробуйте еще раз.</b>",
                                     reply_markup=BACK_KEYBOARD)
        await state.update_data(cancel_msgID=msg.message_id)


@dp.message_handler(state=Form.get_exp_card)
async def add_card_cvv_get(message, state: FSMContext):
    async with state.proxy() as cancel:
        await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=cancel["cancel_msgID"],
                                            reply_markup=InlineKeyboardMarkup([[]]))
    BACK_KEYBOARD = InlineKeyboardMarkup()
    BACK_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-personal-account"))
    try:
        if int(message.text.split("/")[0]) <= 12 and int(message.text.split("/")[1]) % 1000 >= int(
                str(datetime.date.today().year)[2:]):
            await state.update_data(
                get_exp_card=f"{message.text.split('/')[0]}/{int(message.text.split('/')[1]) % 1000}")
            await Form.get_cvv_card.set()
            msg = await bot.send_message(chat_id=message.chat.id, text="<b>Укажите cvv карты</b>",
                                         reply_markup=BACK_KEYBOARD)
            await state.update_data(cancel_msgID=msg.message_id)
        else:
            raise Exception
    except Exception:
        msg = await bot.send_message(chat_id=message.chat.id, text="<b>Не подходит по формату, попробуйте еще раз</b>",
                                     reply_markup=BACK_KEYBOARD)
        await state.update_data(cancel_msgID=msg.message_id)


@dp.message_handler(state=Form.get_cvv_card)
async def add_card_process(message, state: FSMContext):
    async with state.proxy() as cancel:
        await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=cancel["cancel_msgID"],
                                            reply_markup=InlineKeyboardMarkup([[]]))
    if len(message.text) == 3 and message.text.isdigit():
        await state.update_data(get_cvv_card=message.text)
        async with state.proxy() as data:
            cur.execute("INSERT INTO cards (user_id, card_number, exp, cvv) VALUES (%s, %s, %s, %s)",
                        (message.chat.id, data["get_number_card"],
                         data["get_exp_card"], data["get_cvv_card"]))
            conn.commit()

        if "linked_account" in data.keys():
            GET_ACCOUNT_KEYBOARD = InlineKeyboardMarkup()
            GET_ACCOUNT_KEYBOARD.add(InlineKeyboardButton(text="Вернуться в аккаунт", callback_data=f"select-account_{data['linked_account']}"))
        else:
            GET_ACCOUNT_KEYBOARD = InlineKeyboardMarkup()

        await state.finish()
        await bot.send_message(chat_id=message.chat.id, text="<b>Карта добавлена</b>", reply_markup=GET_ACCOUNT_KEYBOARD)
    else:

        BACK_KEYBOARD = InlineKeyboardMarkup()
        BACK_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-personal-account"))

        msg = await bot.send_message(chat_id=message.chat.id, text="<b>Не подходит по формату, попробуйте еще раз</b>",
                                     reply_markup=BACK_KEYBOARD)
        await state.update_data(cancel_msgID=msg.message_id)


@dp.callback_query_handler(lambda call: call.data == "my-accounts" or call.data == "back-to-services" or call.data == "paginator-back")
async def my_accounts(call):
    try:
        if call.data == "paginator-back":
            await Paginator().remover(user_id=str(call.message.chat.id), item_id=str(call.message.message_id))
        ACCOUNT_KEYBOARD = InlineKeyboardMarkup()
        ACCOUNT_KEYBOARD.add(InlineKeyboardButton(text="🟣 Юрент", callback_data="urent-accounts"))
        ACCOUNT_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-personal-account"))

        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="<b>Выберите сервис:</b>", reply_markup=ACCOUNT_KEYBOARD)
    except Exception:
        ...


@dp.callback_query_handler(lambda call: call.data == 'urent-accounts' or call.data == "back-ur-accounts")
async def urent_accounts(call):
    cur.execute("SELECT * FROM ur_accounts WHERE user_id=%s", (call.message.chat.id,))
    account_info = cur.fetchall()
    if not account_info:
        ACCOUNT_KEYBOARD = InlineKeyboardMarkup()
        ACCOUNT_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-services"))
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="<b>На данный момент у вас нет аккаунтов.</b>", reply_markup=ACCOUNT_KEYBOARD)
    else:
        account_info = sorted(account_info, reverse=True, key=lambda x: x[~0])
        if len(account_info) > 4:
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="<b>Ваши аккаунты:</b>",
                                    reply_markup=(await paginator(page=1,
                                                                  array=[[item[0] for item in account_info][i:i + 4] for i in arange(0, len(account_info), 4)],
                                                                  add_down=InlineKeyboardMarkup().add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="paginator-back")),
                                                                  call_data="paginator",
                                                                  user_id=str(call.message.chat.id),
                                                                  msg_id=str(call.message.message_id),
                                                                  spliter="_")))

        else:
            ACCOUNTS_KB = InlineKeyboardMarkup(row_width=2)
            ACCOUNTS_KB.add(*[InlineKeyboardButton(text=item[0], callback_data=f"select-account_{item[0]}") for item in account_info])
            ACCOUNTS_KB.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-services"))
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        text="<b>Ваши аккаунты:</b>", reply_markup=ACCOUNTS_KB)


@dp.callback_query_handler(lambda call: call.data.split("_")[0] in ["select-account", "update-ur-info", "cancel-ur-ride", "paginator"], state="*")
async def selected_account_info(call, state: FSMContext):
    try:
        await state.finish()
        if call.data.split("_")[0] == "paginator":
            await Paginator().remover(user_id=str(call.message.chat.id), item_id=str(call.message.message_id))

        cur.execute("SELECT * FROM ur_accounts WHERE phone_number=%s", (call.data.split("_")[1],))
        account_info = cur.fetchall()[0]
        async with aiohttp.ClientSession() as session:
            urapi = UrentApi(refresh_token=account_info[1], phone_number=call.data.split("_")[1], session=session)
            access_headers = await urapi.get_access_token()
            payment_profile = await urapi.get_payment_profile(access_headers)
            activity = await urapi.get_activity(access_headers)

        MURENTPROFILE_KEYBOARD = InlineKeyboardMarkup()     # Manage urent profile

        if call.data.split("_")[0] == "update-ur-info":
            await call.answer(text='Информация обновлена.', show_alert=True)

        if len(activity["activities"]) == 0:
            MURENTPROFILE_KEYBOARD.add(InlineKeyboardButton(text="Начать поездку", callback_data=f"start-ur-ride_{account_info[0]}"))
            MURENTPROFILE_KEYBOARD.add(InlineKeyboardButton(text="Отвязать карту", callback_data=f"unlink-card-ask_{call.data.split('_')[1]}") if len(payment_profile['cards']) != 0 else
                                       InlineKeyboardButton(text="Привязать карту", callback_data=f"link-card-ask_{call.data.split('_')[1]}"))

        else:
            MURENTPROFILE_KEYBOARD.add(InlineKeyboardButton(text="Завершить поездку", callback_data=f"end-ur-ride_{account_info[0]}"))
            MURENTPROFILE_KEYBOARD.add(InlineKeyboardButton(text="Приостановить поездку", callback_data=f"stop-ur-ride_{account_info[0]}") if activity["activities"][0]["status"] == "Ordering" else
                                       InlineKeyboardButton(text="Возобновить поездку", callback_data=f"resume-ur-ride_{account_info[0]}"))

        MURENTPROFILE_KEYBOARD.add(InlineKeyboardButton(text="♻ Обновить информацию", callback_data=f"update-ur-info_{call.data.split('_')[1]}"))
        MURENTPROFILE_KEYBOARD.add(InlineKeyboardButton(text="❌ Удалить аккаунт", callback_data=f"delete-ur-account_{call.data.split('_')[1]}"))
        MURENTPROFILE_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-ur-accounts"))
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"<b>📞 Номер телефона: <code>{call.data.split('_')[1]}</code></b>\n"
                                                                                                           f"<b>🟣 Количество баллов: <code>{payment_profile['bonuses']['value']}</code></b>\n"
                                                                                                           f"<b>🛴 Самокат: <code>{activity['activities'][0]['bikeIdentifier'].replace('S.', '') if len(activity['activities'][:2]) != 0 else 'Нет'}</code></b>\n"
                                                                                                           f"<b>💳 Карта: <code>{payment_profile['cards'][0]['cardNumber'] if len(payment_profile['cards']) != 0 else 'Нет'}</code></b>", reply_markup=MURENTPROFILE_KEYBOARD)
        await state.update_data(payment_data=payment_profile['bonuses']['value'])
    except Exception:
        print(traceback.format_exc())


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == 'end-ur-ride')
async def end_ur_ride(call, state: FSMContext):
    try:
        cur.execute("SELECT * FROM ur_accounts WHERE phone_number=%s", (call.data.split("_")[1],))
        account_info = cur.fetchall()[0]
        async with aiohttp.ClientSession() as session:
            urapi = UrentApi(refresh_token=account_info[1], phone_number=call.data.split("_")[1], session=session)
            access_headers = await urapi.get_access_token()
            activity = await urapi.get_activity(access_headers)
            locations = choice([{"lat": 44.99708938598633, "lng": 39.07448959350586},
                                {"lat": 45.01229183333333, "lng": 39.07393233333333},
                                {"lat": 44.55036283333334, "lng": 38.0856945},
                                {"lat": 44.5753125, "lng": 38.066902166666665},
                                {"lat": 44.87790683333333, "lng": 37.33355566666667},
                                {"lat": 44.90170366666666, "lng": 37.3204025},
                                {"lat": 43.41010516666667, "lng": 39.936585666666666},
                                {"lat": 43.387023500000005, "lng": 39.99113166666667},
                                {"lat": 43.90788650512695, "lng": 39.3329963684082},
                                {"lat": 43.920260999999996, "lng": 39.31842066666666},
                                ])
            data = {
                  "locationLat": locations["lat"],
                  "locationLng": locations["lng"],
                  "Identifier": activity['activities'][0]['bikeIdentifier'],

                }

            order_end = await urapi.order_end(access_headers=access_headers, data=data)
            if order_end["errors"]:
                await call.answer(f'{" ".join(order_end["errors"][0]["value"])}.', show_alert=True)
                logger.log("END-UR-RIDE", f"{call.message.chat.id} | {call.data.split('_')[1]} | {' '.join(order_end['errors'][0]['value'])}")
            else:
                await call.answer("Поездка завершена.", show_alert=True)
                logger.log("END-UR-RIDE", f"{call.message.chat.id} | {call.data.split('_')[1]} | successfully")
        await selected_account_info(call=call, state=state)
    except Exception:
        print(traceback.format_exc())


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "stop-ur-ride")
async def stop_ur_ride(call, state: FSMContext):
    cur.execute("SELECT * FROM ur_accounts WHERE phone_number=%s", (call.data.split("_")[1],))
    account_info = cur.fetchall()[0]
    async with aiohttp.ClientSession() as session:
        urapi = UrentApi(refresh_token=account_info[1], phone_number=call.data.split("_")[1], session=session)
        access_headers = await urapi.get_access_token()
        activity = await urapi.get_activity(access_headers)
        data = {
              "locationLat": activity["activities"][0]["location"]["lat"],
              "locationLng": activity["activities"][0]["location"]["lng"],
              "isQrCode": False,
              "rateId": "",
              "Identifier": activity['activities'][0]['bikeIdentifier'],
              "withInsurance": False
            }

        req_order_wait = await urapi.order_wait(access_headers=access_headers, data=data)

    logger.log("PAUSE-UR-RIDE", f"{call.message.chat.id} | {call.data.split('_')[1]}")
    await selected_account_info(call=call, state=state)


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "resume-ur-ride")
async def resume_ur_ride(call, state: FSMContext):
    cur.execute("SELECT * FROM ur_accounts WHERE phone_number=%s", (call.data.split("_")[1],))
    account_info = cur.fetchall()[0]
    async with aiohttp.ClientSession() as session:
        urapi = UrentApi(refresh_token=account_info[1], phone_number=call.data.split("_")[1], session=session)
        access_headers = await urapi.get_access_token()
        activity = await urapi.get_activity(access_headers)
        data = {
              "locationLat": activity["activities"][0]["location"]["lat"],
              "locationLng": activity["activities"][0]["location"]["lng"],
              "isQrCode": False,
              "rateId": "",
              "Identifier": activity['activities'][0]['bikeIdentifier'],
              "withInsurance": False
            }

        req_order_resume = await urapi.order_resume(access_headers=access_headers, data=data)
    logger.log("RESUME-UR-RIDE", f"{call.message.chat.id} | {call.data.split('_')[1]}")
    await selected_account_info(call=call, state=state)


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "link-card-ask")
async def link_card_ask(call, state: FSMContext):

    cur.execute("SELECT * FROM cards WHERE user_id=%s", (call.message.chat.id,))
    cards_info = cur.fetchall()
    await state.update_data(account_number=call.data.split("_")[1],
                            linked_account=call.data.split("_")[1])
    if not cards_info:
        CARD_KEYBOARD = InlineKeyboardMarkup()
        CARD_KEYBOARD.add(InlineKeyboardButton(text="Добавить карту", callback_data="add-card"))
        CARD_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data=f"select-account_{call.data.split('_')[1]}"))
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="<b>На данный момент у вас нет привязанных карт.</b>",
                                    reply_markup=CARD_KEYBOARD)
    else:
        CARD_KEYBOARD = InlineKeyboardMarkup(row_width=1)
        CARD_KEYBOARD.add(*[InlineKeyboardButton(text=item[1], callback_data=f"link-card_{item[1]}") for item in cards_info])
        CARD_KEYBOARD.add(InlineKeyboardButton(text="Добавить карту", callback_data="add-card"))
        CARD_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data=f"select-account_{call.data.split('_')[1]}"))
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="<b>Ваши карты:</b>", reply_markup=CARD_KEYBOARD)


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "link-card")
async def link_card(call, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        async with state.proxy() as data:
            cur.execute("SELECT * FROM ur_accounts WHERE phone_number=%s", (data["account_number"],))
            account_info = cur.fetchall()[0]
            cur.execute("SELECT * FROM cards WHERE card_number=%s and user_id=%s", (call.data.split("_")[1], call.message.chat.id, ))
            card_info = cur.fetchall()[0]
            await bot.edit_message_text(chat_id=call.message.chat.id, text="<b>Ожидайте...</b>",
                                        message_id=call.message.message_id,
                                        reply_markup=InlineKeyboardMarkup([[]]))
            urapi = UrentApi(refresh_token=account_info[1], phone_number=data["account_number"], session=session)
            access_headers = await urapi.get_access_token()
            payment_profile = await urapi.get_payment_profile(access_headers=access_headers)
            cryptogram = await urapi.cloudpayments_card(access_headers=access_headers, card_info={
                "card_number": card_info[1],
                "exp": f"{card_info[2][~1:]}{card_info[2][:2]}",
                "cvv": card_info[3]}, public_id=payment_profile["cloudPaymentsPublicId"])
            print(cryptogram)
            # if "api.cloudpayments.ru" in cryptogram['acsUrl']:
            #     set_browser_info = await urapi.set_browser_info(cryptogram=cryptogram)
            #     post3ds = await urapi.post_3dsecure(access_headers=access_headers,
            #                                         cryptogram=cryptogram)
            #     if post3ds["errors"] is not []:
            #         await call.answer(" ".join(post3ds["errors"][0]["value"]), show_alert=True)
            #     call.data = f"select-account_{data['account_number']}"
            #     await selected_account_info(call, state)
            # else:
            link = await urapi.link_card3ds(data={
                "payment_url": cryptogram["acsUrl"],
                "pa_req": cryptogram["paReq"],
                "md": cryptogram["md"],
            })
            CHECK_KEYBOARD = InlineKeyboardMarkup()
            CHECK_KEYBOARD.add(InlineKeyboardButton(text="Перейти к привязке", web_app=WebAppInfo(url=link["url"])))
            CHECK_KEYBOARD.add(InlineKeyboardButton(text="Проверить привязку", callback_data=f"check-link_{link['url'].split('=')[1]}"))
            await bot.edit_message_text(chat_id=call.message.chat.id, text="<b>Перейдите по ссылке для привязки</b>",
                                        message_id=call.message.message_id,
                                        reply_markup=CHECK_KEYBOARD)


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "check-link")
async def check_link_card(call, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        async with state.proxy() as data:
            cur.execute("SELECT * FROM ur_accounts WHERE phone_number=%s", (data["account_number"],))
            account_info = cur.fetchall()[0]
            urapi = UrentApi(refresh_token=account_info[1], phone_number=data["account_number"], session=session)
            access_headers = await urapi.get_access_token()
            check_card = await urapi.check_card3ds(card3ds_id=call.data.split("_")[1])
            post3ds = await urapi.post_3dsecure(access_headers=access_headers, data={
            "md": check_card["content"]["md"],
            "paRes": check_card["content"]["pa_res"]
            })
            if post3ds["errors"]:
                print(post3ds["errors"])
                await call.answer(f'{" ".join(post3ds["errors"][0]["value"])}.', show_alert=True)

            logger.log("LINK-CARD", f"{call.message.chat.id} | {data['account_number']}")
            call.data = f'select-account_{data["account_number"]}'
            await selected_account_info(call, state)


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "unlink-card-ask")
async def unlink_card_ask(call):
    YES_OR_NO_KB = InlineKeyboardMarkup()
    YES_OR_NO_KB.add(InlineKeyboardButton(text="✅ Да", callback_data=f"unlink-card_{call.data.split('_')[1]}"),
                     InlineKeyboardButton(text="❌ Нет", callback_data=f"select-account_{call.data.split('_')[1]}"))

    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                text="<b>Вы уверены что хотите удалить карту?</b>", reply_markup=YES_OR_NO_KB)


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "unlink-card")
async def unlink_card_process(call, state: FSMContext):
    cur.execute("SELECT * FROM ur_accounts WHERE phone_number=%s", (call.data.split("_")[1],))
    account_info = cur.fetchall()[0]
    async with aiohttp.ClientSession() as session:
        urapi = UrentApi(refresh_token=account_info[1], phone_number=call.data.split("_")[1], session=session)
        access_headers = await urapi.get_access_token()
        del_card = await urapi.delete_card(access_headers)
        await call.answer(text='Успешно отвязано.', show_alert=True)
        logger.log("UNLINK-CARD", f"{call.message.chat.id} | {call.data.split('_')[1]}")
        await selected_account_info(call=call, state=state)


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "start-ur-ride")
async def get_scooter_id(call, state: FSMContext):
    try:
        await state.update_data(get_scooter=call.data.split("_")[1])
        CANCEL_KEYBOARD = InlineKeyboardMarkup()
        CANCEL_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data=f"cancel-ur-ride_{call.data.split('_')[1]}"))
        await Form.get_scooter.set()
        msg = await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="<b>Пришлите QR код или номер самоката текстом</b>", reply_markup=CANCEL_KEYBOARD)
        await state.update_data(cancel_msgID=msg.message_id)
    except Exception:
        print(traceback.format_exc())


@dp.message_handler(state=Form.get_scooter, content_types=["text"])
async def start_ride_process_text(message, state: FSMContext, req=False):
    try:
        async with state.proxy() as data:
            await state.finish()
            if not req:
                await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=data["cancel_msgID"],
                                                reply_markup=InlineKeyboardMarkup([[]]))
            cur.execute("SELECT * FROM ur_accounts WHERE phone_number=%s", (data["get_scooter"],))
            account_info = cur.fetchall()[0]

        async with aiohttp.ClientSession() as session:
            urapi = UrentApi(refresh_token=account_info[1], phone_number=data["get_scooter"], session=session)
            access_headers = await urapi.get_access_token()
            profile = await urapi.get_urent_profile(access_headers=access_headers)
            scooter_info = await urapi.get_scooter_info(scooter_id=message.text.replace("-", ""), access_headers={**access_headers, **{"ur-user-id": profile["id"]}})
        RATE_KEYBOARD = InlineKeyboardMarkup(row_width=1)

        RATE_KEYBOARD.add(InlineKeyboardButton(text="⛔ Отключить автозавершение", callback_data="off-autostop"))
        RATE_KEYBOARD.add(*[InlineKeyboardButton(text=f'{item["displayName"]} {str(item["activationCost"]["value"])+" + " if item["activationCost"] != None else " "}{item["debit"]["valueFormatted"]}',
                                                 callback_data=f"select-ur-rate_{item['id']}_auto") for item in scooter_info["rate"]["entries"]])
        RATE_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data=f'select-account_{data["get_scooter"]}'))
        pprint(RATE_KEYBOARD)
        await state.update_data(get_scooter={
            "make_data": {
                "locationLat": scooter_info["location"]["lat"],
                "locationLng": scooter_info["location"]["lng"],
                "isQrCode": False,
                "Identifier": message.text.replace("-", ""),
                "withInsurance": False
            },
            "phone": data["get_scooter"],
            "access_headers": {**access_headers, **{"ur-user-id": profile["id"]}},
            "debit_info": scooter_info["rate"]["entries"]},
            payment_data=data["payment_data"])

        await bot.send_message(chat_id=message.chat.id, text=f"<b>🛴 Номер самоката: <code>{message.text.replace('-', '')}</code></b>\n"
                                                             f"<b>⚡ Заряд: {int(scooter_info['charge']['batteryPercent'] * 100)}%\n"
                                                             f"<b>💳 Залог: {scooter_info['rate']['entries'][0]['verifyCost']['valueFormattedWithoutZero']}</b>\n"
                                                             f"<tg-spoiler>Примерно хватит на {round(scooter_info['charge']['remainKm'], 2)} км</tg-spoiler></b>", reply_markup=RATE_KEYBOARD)
    except Exception:
        await bot.send_message(chat_id=message.chat.id, text=f"<b>{' '.join(scooter_info['errors'][0]['value'])}</b>")
        print(traceback.format_exc())


@dp.callback_query_handler(lambda call: call.data == "off-autostop")
async def off_autostop(call, state: FSMContext):
    try:
        await call.answer("Автозавершение выключено", show_alert=True)
        RATE_KEYBOARD = InlineKeyboardMarkup()
        RATE_KEYBOARD.add(InlineKeyboardButton(text="✅ Включить автозавершение", callback_data="on-autostop"))
        for num, kb in enumerate(call.message.reply_markup.inline_keyboard[1:~0]):
            RATE_KEYBOARD.add(InlineKeyboardButton(text=call.message.reply_markup.inline_keyboard[num + 1][0]["text"], callback_data=call.message.reply_markup.inline_keyboard[num + 1][0]["callback_data"].replace("auto", "hand")))
        RATE_KEYBOARD.add(InlineKeyboardButton(text=call.message.reply_markup.inline_keyboard[~0][0]["text"], callback_data=call.message.reply_markup.inline_keyboard[~0][0]["callback_data"]))
        await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=RATE_KEYBOARD)
    except Exception:
        print(traceback.format_exc())


@dp.callback_query_handler(lambda call: call.data == "on-autostop")
async def on_autostop(call, state: FSMContext):
    try:
        await call.answer("Автозавершение включено", show_alert=True)
        RATE_KEYBOARD = InlineKeyboardMarkup()
        RATE_KEYBOARD.add(InlineKeyboardButton(text="⛔ Отключить автозавершение", callback_data="off-autostop"))
        for num, kb in enumerate(call.message.reply_markup.inline_keyboard[1:~0]):
            RATE_KEYBOARD.add(InlineKeyboardButton(text=call.message.reply_markup.inline_keyboard[num + 1][0]["text"], callback_data=call.message.reply_markup.inline_keyboard[num + 1][0]["callback_data"].replace("hand", "auto")))
        RATE_KEYBOARD.add(InlineKeyboardButton(text=call.message.reply_markup.inline_keyboard[~0][0]["text"], callback_data=call.message.reply_markup.inline_keyboard[~0][0]["callback_data"]))
        await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=RATE_KEYBOARD)
    except Exception:
        print(traceback.format_exc())


@dp.message_handler(state=Form.get_scooter, content_types=["photo"])
async def start_ride_process_photo(message, state: FSMContext):
    async with state.proxy() as cancel:
        await state.finish()
        await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=cancel["cancel_msgID"],
                                            reply_markup=InlineKeyboardMarkup([[]]))
        await state.update_data(cancel_msgID=cancel["cancel_msgID"])
        await state.update_data(get_scooter=cancel["get_scooter"])
    try:
        await message.photo[-1].download(destination_file=f'temp/photo_{message.chat.id}.png')
        img = cv2.imread(f"temp/photo_{message.chat.id}.png")
        qrcodes = pyzbar.decode(img)
        os.remove(f"temp/photo_{message.chat.id}.png")
        message.text = qrcodes[0].data.decode().lower().split("s.")[1]

        await start_ride_process_text(message, state, req=True)

    except Exception:
        await bot.send_message(chat_id=message.chat.id, text="<b>Что то пошло не так... Проверьте, хорошо ли видно QR код самоката.</b>")
        print(traceback.format_exc())


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "select-ur-rate")
async def starter_ur_ride(call, state: FSMContext):
    try:
        async with state.proxy() as data:
            await state.finish()
            scores = data['payment_data']
            data = data["get_scooter"]

        call_mode = call.data.split("_")
        async with aiohttp.ClientSession() as session:
            urapi = UrentApi(session=session)
            order_make = await urapi.order_make(access_headers=data["access_headers"], data={**data["make_data"], **{"rateId": call.data.split("_")[1]}})
            if order_make["errors"]:
                await call.answer(f'{" ".join(order_make["errors"][0]["value"])}.', show_alert=True)
                logger.log("START-UR-RIDE", f"{call.message.chat.id} | {data['phone']} | {' '.join(order_make['errors'][0]['value'])}")
            else:
                await call.answer("Поездка начата.", show_alert=True)
                logger.log("START-UR-RIDE", f"{call.message.chat.id} | {data['phone']} | successfully")

        call.data = f'select-account_{data["phone"]}'
        await selected_account_info(call=call, state=state)

        if call_mode[2] == "auto":
            print("AUTO")
            selected_rate = next((x for x in data["debit_info"] if x["id"] == call_mode[1]), None)
            max_time = max(round(((scores - (float(selected_rate["activationCost"]['value']) if selected_rate["activationCost"] is not None else 0)) / float(selected_rate["debit"]["value"])) * 60) - 10, 0)
            print(max_time)
            await auto_completion(call, state, max_time, data["phone"])
        else:
            print("HAND")

    except Exception:
        print(traceback.format_exc())


async def auto_completion(call, state: FSMContext, maxtime, phone):
    try:
        await asyncio.sleep(maxtime)
        call.data = f"end-ur-ride_{phone}"
        await end_ur_ride(call, state)
    except Exception:
        print(traceback.format_exc())


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "delete-ur-account")
async def delete_ur_account(call):
    DELETE_KEYBOARD = InlineKeyboardMarkup()
    DELETE_KEYBOARD.add(InlineKeyboardButton(text="✅ Да", callback_data=f"delete-ur_{call.data.split('_')[1]}"), InlineKeyboardButton(text="❌ Нет", callback_data=f"select-account_{call.data.split('_')[1]}"))
    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="<b>Вы уверены что хотите удалить этот аккаунт?</b>", reply_markup=DELETE_KEYBOARD)


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "delete-ur")
async def delete_ur_account(call, state: FSMContext):
    cur.execute("SELECT * FROM ur_accounts WHERE phone_number=%s", (call.data.split("_")[1],))
    account_info = cur.fetchall()[0]
    async with aiohttp.ClientSession() as session:
        urapi = UrentApi(refresh_token=account_info[1], phone_number=call.data.split("_")[1], session=session)
        access_headers = await urapi.get_access_token()
        del_account = await urapi.delete_account(access_headers=access_headers)
    cur.execute("DELETE FROM ur_accounts WHERE phone_number=%s", (call.data.split("_")[1], ))
    conn.commit()
    await my_accounts(call)


@dp.callback_query_handler(lambda call: call.data == "replenish-balance",  state="*")
async def replenish_balance(call, state: FSMContext):

    await state.finish()
    SELECT_PAYMENT_METOD_KB = InlineKeyboardMarkup()
    SELECT_PAYMENT_METOD_KB.row(InlineKeyboardButton(text="💳 QIWI/CARD", callback_data="payment_qiwi"), InlineKeyboardButton(text="🟢 LOLZTEAM", callback_data="payment_lolz"))
    SELECT_PAYMENT_METOD_KB.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-personal-account"))
    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="<b>💸 Выберите платежную систему для пополнения:</b>", reply_markup=SELECT_PAYMENT_METOD_KB)


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "payment")
async def payment(call, state: FSMContext):
    CANCEL_KEYBOARD = InlineKeyboardMarkup()
    CANCEL_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="replenish-balance"))
    if call.data.split("_")[1] == "qiwi": # callback_data >> payment_qiwi
        await Form.get_amount_qiwi.set()
    elif call.data.split("_")[1] == "lolz":
        await Form.get_amount_lolz.set()
    msg = await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="<b>Введите число на которое хотите пополнить свой баланс:</b>",
                                      reply_markup=CANCEL_KEYBOARD)
    await state.update_data(cancel_msgID=msg.message_id)


@dp.message_handler(state=Form.get_amount_lolz)
async def send_req_replenish_lolz(message, state: FSMContext):
    async with state.proxy() as cancel:
        await state.finish()
        await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=cancel["cancel_msgID"],
                                            reply_markup=InlineKeyboardMarkup([[]]))
    if message.text.isdigit():
        uuid = uuid4().hex
        BILL_KEYBAORD = InlineKeyboardMarkup()
        BILL_KEYBAORD.add(InlineKeyboardButton(text="💸 Пополнить", web_app=WebAppInfo(url=(await lolz.get_link(amount=message.text, comment=uuid)))))
        BILL_KEYBAORD.add(InlineKeyboardButton(text="♻ Проверить оплату", callback_data=f"check-paid_{uuid}"))
        await bot.send_message(chat_id=message.chat.id, text=f"<b>💳 Способ оплаты через LOLZTEAM.\n"
                                                             f"💵 Сумма: <code>{message.text} руб.</code>\n\n"
                                                             f"⛔Ни в коем случае не меняйте комментарий к переводу так как "
                                                             f"по нему происходит проверка платежа⛔</b>", reply_markup=BILL_KEYBAORD)
    else:
        return await bot.send_message(message.chat.id, "<b>Сумма введена не верно, пополнение отменено.</b>")


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "check-paid")
async def check_paid(call):
    try:
        payment = await lolz.check_payments(comment=call.data.split("_")[1])
        pprint(payment)
        if "error" not in payment and payment:
            for item in payment:
                if item['payment_status'] == "success_in" and item["data"]["comment"] == call.data.split("_")[1]:

                    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                text=f"<b>💰 Баланс успешно пополнился на сумму <code>{item['incoming_sum']} ₽</code></b>",
                                                reply_markup=InlineKeyboardMarkup([[]]))

                    cur.execute("SELECT * FROM users_info WHERE user_id=%s", (call.message.chat.id,))
                    user_info = cur.fetchall()[0]
                    if user_info[6] != 0:
                        cur.execute("UPDATE users_info SET earning_referrals=earning_referrals + %s WHERE user_id=%s",
                                    (int(int(item['incoming_sum']) * 0.25), user_info[6]))
                    cur.execute("UPDATE users_info SET balance=balance + %s, total_balance=total_balance+%s WHERE user_id=%s",
                                (int(item['incoming_sum']), int(item['incoming_sum']), call.message.chat.id))
                    cur.execute("UPDATE money SET all_money = all_money + %s", (int(item['incoming_sum']),))
                    conn.commit()
                    logger.log("BALANCE-REPLENISHMENT", f"{call.message.chat.id} | {item['incoming_sum']} | lolz | successfully")
                    await bot.send_message(chat_id=CHANNEL_ID, text=f"<b>Поступило пополнение на LOLZTEAM от @{call.message.chat.username} в размере {item['incoming_sum']} руб.</b>")
                else:
                    await call.answer("❗ Платеж еще не пришел.", show_alert=True)
        else:
            await call.answer("❗ Платеж еще не пришел.", show_alert=True)
    except Exception:
        print(traceback.format_exc())
        await bot.send_message(chat_id=call.message.chat.id, text="Что то пошло не так...")


@dp.message_handler(state=Form.get_amount_qiwi)
async def send_req_replenish_qiwi(message, state: FSMContext):
    async with state.proxy() as cancel:
        await state.finish()
        await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=cancel["cancel_msgID"],
                                            reply_markup=InlineKeyboardMarkup([[]]))
    if message.text.isdigit():
        bill = p2p.bill(amount=int(message.text), lifetime=15, comment=str(message.chat.id))
        BILL_KEYBAORD = InlineKeyboardMarkup()
        # BILL_KEYBAORD.add(InlineKeyboardButton(text="💸 Пополнить", url=bill.pay_url))
        BILL_KEYBAORD.add(InlineKeyboardButton(text="💸 Пополнить", web_app=WebAppInfo(url=bill.pay_url)))
        await bot.send_message(chat_id=message.chat.id, text=f"<b>💳 Способ оплаты через QIWI или карту.</b>\n"
                                                f"<b>💵 Сумма:</b> <code>{message.text} руб.</code>\n"
                                                f"<b>⏱ Время на оплату</b> <code>15 минут.</code>",
                               reply_markup=BILL_KEYBAORD)
        await functionoplata(message=message, bill=bill)
    else:
        return await bot.send_message(message.chat.id, "<b>Сумма введена не верно, пополнение отменено.</b>")


async def functionoplata(message, bill):
    oplata_time = datetime.datetime.now()
    datetime_delta = oplata_time + datetime.timedelta(minutes=15)
    while True:
        try:
            status = p2p.check(bill_id=bill.bill_id).status
            if status == 'PAID':
                await bot.send_message(message.chat.id,
                                       f"<b>💰 Баланс успешно пополнился на сумму</b> <code>{message.text} ₽</code>")
                cur.execute("SELECT * FROM users_info WHERE user_id=%s", (message.chat.id,))
                user_info = cur.fetchall()[0]
                if user_info[6] != 0:
                    cur.execute("UPDATE users_info SET earning_referrals=earning_referrals + %s WHERE user_id=%s",
                                (int(int(message.text) * 0.25), user_info[6]))
                cur.execute("UPDATE users_info SET balance=balance + %s, total_balance=total_balance+%s WHERE user_id=%s",
                            (int(message.text), int(message.text), message.chat.id))
                cur.execute("UPDATE money SET all_money = all_money + %s", (int(message.text),))
                conn.commit()
                logger.log("BALANCE-REPLENISHMENT", f"{message.chat.id} | {message.text} | qiwi | successfully")
                await bot.send_message(chat_id=CHANNEL_ID,
                                       text=f"<b>Поступило пополнение на QIWI от @{message.from_user.username} в размере {message.text} руб.</b>")

                break
            elif datetime.datetime.now() > datetime_delta:
                await bot.send_message(chat_id=message.chat.id, text="<b>Время действия ссылки на оплату истекло.</b>")
                logger.log("BALANCE-REPLENISHMENT", f"{message.chat.id} | {message.text} | Error - time over")
                break
            await asyncio.sleep(3)
        except Exception:
            print(traceback.format_exc())


@dp.callback_query_handler(lambda call: call.data == "referral-system")
async def referral_system(call):
    BACK_KEYBOARD = InlineKeyboardMarkup()
    BACK_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-personal-account"))

    cur.execute('SELECT earning_referrals FROM users_info WHERE user_id=%s', (call.message.chat.id,))
    earning_ref = cur.fetchall()[0][0]

    cur.execute('SELECT user_id FROM users_info WHERE referral=%s', (call.message.chat.id,))
    count_ref = cur.fetchall()

    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                text=f"<b>💸 Заработано на рефералах:</b> <code>{earning_ref} ₽</code>\n"
                                     f"<b>👥 Количество рефералов:</b> <code>{len(count_ref)}</code>\n"
                                     f"<b>❗ Вы будете получать на баланс 25% от пополнений ваших рефералов.</b>\n\n"
                                     f"<b>📣 Ваша реферальная ссылка: </b> <code>https://t.me/{call.message.from_user.username}?start={call.message.chat.id}</code>\n",
                                reply_markup=BACK_KEYBOARD)


@dp.callback_query_handler(lambda call: call.data == "back-to-personal-account", state="*")
async def back_to_personal_account(call, state: FSMContext):
    await state.finish()
    await personal_account(call.message, req=True)


@dp.message_handler(lambda message: message.text == "💬 Информация")
@rate_limit(limit=3, key="info")
# @dp.throttled(anti_flood, rate=3)
@is_baned
async def help_panel(message, req=False, **kwargs):
    HELP_KEYBOARD = InlineKeyboardMarkup()
    HELP_KEYBOARD.add(InlineKeyboardButton(text="🆘 Техническая поддержка", url=USERNAME_FOR_HELP))
    HELP_KEYBOARD.add(InlineKeyboardButton(text="🔔 Канал", url=CHANNEL_FOR_HELP),
                      InlineKeyboardButton(text="📋 Правила ", callback_data="rules"))
    HELP_KEYBOARD.add(InlineKeyboardButton(text="🟢 Тема на LOLZTEAM", web_app=WebAppInfo(url=TOPIC_ON_LOLZ_FOR_HELP)))
    if not req:
        await bot.send_message(chat_id=message.chat.id, text="<b>❕ Познавательная вкладка</b>", reply_markup=HELP_KEYBOARD)
    else:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="<b>❕ Познавательная вкладка</b>", reply_markup=HELP_KEYBOARD)


@dp.callback_query_handler(lambda call: call.data == "back-to-help-panel")
async def back_to_help_panel(call):
    await help_panel(call.message, req=True)


@dp.callback_query_handler(lambda call: call.data == "rules")
async def open_rules(call):
    BACK_KEYBOARD = InlineKeyboardMarkup()
    BACK_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-help-panel"))

    text = "<b>📖 Обязательные правила.</b>\n" \
           "<code>1.1. Возврат денежных средств возвращается только на баланс бота.</code>\n" \
           "<code>1.2. Внутренний баланс в боте вывести нельзя.</code>\n" \
           "<code>1.3 Неведение правил не освобождает вас об ответственности.</code>\n" \
           "<b>🛍 Покупка товара. https://t.me/end_soft</b>\n" \
           "<code>2.1. Нажимая кнопку «Подтвердить покупку» вы подтверждаете свои действия.</code>\n" \
           "<code>2.2. Прежде чем покупать обязательно ознакомьтесь с инструкцией товара.</code>\n" \
           "<code>2.3. Если возникли проблемы покупатель, как можно быстрее должен написать в техническую поддержку.</code>\n" \
           "<b>🎁 Гарантия товара.</b>\n" \
           "<code>3.1. Гарантия товара начинается сразу же после покупки.</code>\n" \
           "<code>3.2 После гарантийного срока товар к возврату не подлежит.</code>\n" \
           "<b>📋 Пользовательское соглашение.</b>\n" \
           "<code>4.1. Совершая покупки в боте, вы подтверждаете что автоматически согласны с вышеперечисленными правилами нашего сервиса.</code>\n" \
           "<code>4.2. Пользуясь ботом вы автоматически даете согласие на обработку персональных данных согласно Федеральному закону 'О персональных данных' от 27.07.2006 N 152-ФЗ.</code>"

    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text,
                                reply_markup=BACK_KEYBOARD)


@dp.callback_query_handler(lambda call: call.data == "activate-promo")
async def process_activate_promo(call, state: FSMContext):
    CANCEL_KEYBOARD = InlineKeyboardMarkup()
    CANCEL_KEYBOARD.add(InlineKeyboardButton(text="🔙 Вернуться", callback_data="back-to-personal-account"))
    await Form.get_promo_for_activate.set()
    msg = await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="<b>🎁 Введите промокод:</b>", reply_markup=CANCEL_KEYBOARD)
    await state.update_data(cancel_msgID=msg.message_id)


@dp.message_handler(state=Form.get_promo_for_activate)
async def activate_promo(message, state: FSMContext):
    try:
        async with state.proxy() as cancel:
            await state.finish()
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=cancel["cancel_msgID"],
                                                reply_markup=InlineKeyboardMarkup([[]]))
        cur.execute("SELECT * FROM promocodes WHERE name=%s", (message.text,))
        promo_info = cur.fetchall()[0]
        ids = json.loads(promo_info[3])
        if message.chat.id not in ids["ids"]:
            if promo_info[1] == 1:
                cur.execute("DELETE FROM promocodes WHERE name=%s", (message.text,))
            else:
                cur.execute("UPDATE promocodes SET number_of_uses=number_of_uses-1, used_ids=%s WHERE name=%s", (json.dumps({"ids": ids["ids"] + [message.chat.id]}), message.text))
            cur.execute("UPDATE users_info SET balance=balance+%s, total_balance=total_balance+%s WHERE user_id=%s",
                        (promo_info[2], promo_info[2], message.from_user.id))
            conn.commit()
            await bot.send_message(chat_id=message.chat.id,
                                   text=f"<b>🟢 Промокод успешно введен, вам на баланс зачислилось <code>{promo_info[2]}</code> р.</b>",
                                   reply_markup=MAIN_KEYBOARD)
            logger.log("ACTIVATE-PROMOCODE", f"{message.chat.id} | {message.text} | successfully")
        else:
            await bot.send_message(chat_id=message.chat.id, text="<b>Вы уже использовали этот промокод!</b>")
            logger.log("ACTIVATE-PROMOCODE", f"{message.chat.id} | {message.text} | Error - used")
    except Exception:
        await bot.send_message(chat_id=message.chat.id, text="<b>🔴 Промокод не найден.</b>",
                               reply_markup=MAIN_KEYBOARD)
        logger.log("ACTIVATE-PROMOCODE", f"{message.chat.id} | {message.text} | Error - not found")
