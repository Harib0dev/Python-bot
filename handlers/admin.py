# EndSoft - https://t.me/end_soft
import asyncio
import datetime
import json
import re
import time
import traceback
import uuid
import math
from collections import Counter
from functools import reduce
from random import choice, randint
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
from aiogram.utils import executor
from aiogram.types.web_app_info import WebAppInfo
from aiogram.utils.exceptions import Throttled
from loader import *
from numpy import arange
from utils.is_status import *
# from api.sms_activate import SMSActivate
from api.sms_activator import SMSActivator
from api.urent import UrentApi
from pprint import pprint
import os
from .user import selected_account_info



@dp.callback_query_handler(lambda call: call.data == "cancel",
                           state=[Form.get_user_id, Form.get_issue_money, Form.get_fetch_money, Form.info_promocode,
                                  Form.count_promocodes, Form.name_of_promo, Form.number_of_uses, Form.price_of_promo,
                                  Form.mailing_msg, Form.get_amount_qiwi, Form.get_amount_lolz, Form.get_promo_for_activate,
                                  Form.get_token, Form.get_scooter, Form.get_promocodes,
                                  Form.get_count_account_to_create, Form.get_description, Form.get_price])
async def get_name_process(call, state: FSMContext):
    await state.finish()
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    # await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
    #                                     reply_markup=InlineKeyboardMarkup([[]]))
    # await bot.send_message(chat_id=call.message.chat.id, text=f"<b>Отменено</b>")


@dp.message_handler(commands=["admin"])
@is_admin
async def admin_panel(message, **kwargs):
    await bot.send_message(chat_id=message.chat.id, text="<b>Выберите раздел:</b>", reply_markup=ADMIN_KEYBOARD)


@dp.message_handler(lambda message: message.text == "Невалид")
@is_admin
async def not_valid(message, **kwargs):
    cur.execute("SELECT * FROM ur_accounts WHERE user_id=1")
    GET_NOTVALID = InlineKeyboardMarkup()
    GET_NOTVALID.add(InlineKeyboardButton(text=f"Взять аккаунт | {len(cur.fetchall())} шт.", callback_data="get-notvalid-account"))
    await bot.send_message(chat_id=message.chat.id, text="<b>Нажмите на кнопку для получения не валидного аккаунта\n"
                                                         "Возможные дефекты:\n"
                                                         "→ Уже введенные промокоды\n"
                                                         "→ Привязанная карта</b>", reply_markup=GET_NOTVALID)


@dp.callback_query_handler(lambda call: call.data == "get-notvalid-account")
async def get_notvalid_account(call, state: FSMContext):
    try:
        cur.execute("SELECT * FROM ur_accounts WHERE user_id=1")
        account = choice(cur.fetchall())

        cur.execute("UPDATE ur_accounts SET user_id=%s, get_datetime=%s WHERE phone_number=%s", (call.message.chat.id, datetime.datetime.now(), account[0]))
        conn.commit()
        call.data = f"select-account_{account[0]}"
        await selected_account_info(call=call, state=state)
    except Exception:
        print(traceback.format_exc())
        await call.answer("Что то пошло не так!", show_alert=True)


@dp.message_handler(lambda message: message.text == "Управление юрентом")
@is_admin
async def managing_urent_service(message, **kwargs):
    URENT_KEYBOARD = InlineKeyboardMarkup()
    URENT_KEYBOARD.add(InlineKeyboardButton(text="Создать аккаунты", callback_data="create-ur-accounts"))
    URENT_KEYBOARD.add(InlineKeyboardButton(text="Сменить токен", callback_data="change-token"))
    await bot.send_message(chat_id=message.chat.id, text="<b>Управление юрент</b>", reply_markup=URENT_KEYBOARD)


@dp.callback_query_handler(lambda call: call.data == "create-ur-accounts")
async def create_ur_accounts_get_count(call, state: FSMContext):
    CANCEL_KEYBOARD = InlineKeyboardMarkup()
    CANCEL_KEYBOARD.add(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    await Form.get_count_account_to_create.set()
    msg = await bot.edit_message_text(chat_id=call.message.chat.id,
                                      text="<b>Пришлите количество аккаунтов которые вы хотите создать:</b>",
                                      message_id=call.message.message_id, reply_markup=CANCEL_KEYBOARD)
    await state.update_data(cancel_msgID=msg.message_id)


@dp.message_handler(state=Form.get_count_account_to_create)
async def create_ur_accounts_get_price(message, state: FSMContext):
    try:
        async with state.proxy() as data:
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=data["cancel_msgID"],
                                                reply_markup=InlineKeyboardMarkup([[]]))
        cur.execute("SELECT sms_token FROM tokens")
        token = cur.fetchall()[0][0]
        async with aiohttp.ClientSession() as session:
            sms = SMSActivator(session=session, key=token)
            # service_info = await sms.get_current_price(service="of")  Узнать цену urent => service_info["cost"]
            balance = await sms.get_balance()
            cost = 1
        if balance >= float(message.text) * float(cost):
            CANCEL_KEYBOARD = InlineKeyboardMarkup()
            CANCEL_KEYBOARD.add(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
            await Form.get_price.set()
            msg = await bot.send_message(chat_id=message.chat.id, text="<b>Пришлите цену для аккаунтов</b>",
                                         reply_markup=CANCEL_KEYBOARD)
            await state.update_data(cancel_msgID=msg.message_id)
            await state.update_data(get_token=token)
            await state.update_data(get_count_account_to_create=message.text)
        else:
            await state.finish()
            await bot.send_message(chat_id=message.chat.id, text=f'<b>Недостаточно средств\n'
                                                                 f'Требуется: <code>{float(cost) * float(message.text)}</code> ₽\n'
                                                                 f'Есть: <code>{balance}</code> ₽\n'
                                                                 f'Необходимо пополнить на <code>{(float(cost) * float(message.text) - balance):.2f}</code> ₽</b>')
    except Exception:
        await bot.send_message(chat_id=message.chat.id, text="<b>Что то пошло не так...</b>")
        await state.finish()
        print(traceback.format_exc())


@dp.message_handler(state=Form.get_price)
async def create_ur_account_get_promocodes(message, state: FSMContext):
    try:
        async with state.proxy() as data:
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=data["cancel_msgID"],
                                                reply_markup=InlineKeyboardMarkup([[]]))
        CANCEL_KEYBOARD = InlineKeyboardMarkup()
        CANCEL_KEYBOARD.add(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
        await state.update_data(get_price=int(message.text))
        await Form.get_description.set()
        msg = await bot.send_message(chat_id=message.chat.id, text="<b>Пришлите описание для аккаунтов</b>",
                                     reply_markup=CANCEL_KEYBOARD)
        await state.update_data(cancel_msgID=msg.message_id)
    except Exception:
        print(traceback.format_exc())
        await bot.send_message(chat_id=message.chat.id, text="<b>Что то пошло не так...</b>")
        await state.finish()


@dp.message_handler(state=Form.get_description)
async def create_ur_account_get_description(message, state: FSMContext):
    try:
        async with state.proxy() as data:
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=data["cancel_msgID"],
                                                reply_markup=InlineKeyboardMarkup([[]]))
        CANCEL_KEYBOARD = InlineKeyboardMarkup()
        CANCEL_KEYBOARD.add(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
        await state.update_data(get_description=message.text)
        await Form.get_promocodes.set()
        msg = await bot.send_message(chat_id=message.chat.id, text="<b>Пришлите промокоды в формате "
                                                                   "<code>промокод1|промокод2|промокод3</code></b>",
                                     reply_markup=CANCEL_KEYBOARD)
        await state.update_data(cancel_msgID=msg.message_id)
    except Exception:
        print(traceback.format_exc())
        await bot.send_message(chat_id=message.chat.id, text="<b>Что то пошло не так...</b>")
        await state.finish()


@dp.message_handler(state=Form.get_promocodes)
async def create_ur_account_proccess(message, state: FSMContext):
    try:
        await state.update_data(get_promocodes=message.text.split("|"))

        async with state.proxy() as data:
            await state.finish()
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=data["cancel_msgID"],
                                                reply_markup=InlineKeyboardMarkup([[]]))
            spliter = "\n"
            await bot.send_message(chat_id=message.chat.id,
                                   text=f"<b>Процесс запущен!\n\n"
                                        f"Используемые промокоды:\n"
                                        f"{spliter.join([f'➡      {item}' for item in data['get_promocodes']])}</b>")

        await state.update_data(get_promocodes=data["get_promocodes"])

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(registration_ur_accounts(message=message, token=data["get_token"],
                                                             place=place, price=data["get_price"], description=data["get_description"])) for place in range(int(data["get_count_account_to_create"]))]
        # registration_results = [task.result() for task in tasks]
        # pprint(registration_results)
        # cur.executemany("INSERT INTO ur_accounts (phone_number, refresh_token, price, user_id, description) VALUES (%s, %s, %s, %s, %s)",
        #                 list([(phone, token, data["get_price"], status, data["get_description"]) for phone, token, status in registration_results
        #                       if phone is not None and token is not None and status is not None]))
        # conn.commit()
        # await bot.send_message(chat_id=CHANNEL_ID, text=f'<b>Создание аккаунтов закончено.\n'
        #                                                 f'Было создано {len(list([(phone, token, data["get_price"], status) for phone, token, status in registration_results if phone is not None and token is not None and status is not None]))} аккаунтов</b>')
    except Exception:
        print(traceback.format_exc())


async def registration_ur_accounts(message, token, place, price, description):
    try:
        await asyncio.sleep(place * 3)
        async with aiohttp.ClientSession() as session:
            sms = SMSActivator(session=session, key=token)
            number = await sms.get_number()
            urapi = UrentApi(refresh_token=None, phone_number=f'{number["number"]}', session=session)
            public_token = await urapi.get_public_key()
            mobile_code = await urapi.get_mobile_code(access_headers=public_token)
            pprint(mobile_code)
            end_time = datetime.datetime.now() + datetime.timedelta(minutes=4)
            if len(mobile_code["errors"]) == 0:
                while True:

                    if (sms_code := await sms.get_active_activation(nid=number["id"])) != "":
                        print(sms_code)
                        break
                    if datetime.datetime.now() > end_time:
                        change_status = await sms.change_number_status(activation_id=number["id"], status="1")
                        pprint(change_status)
                        await bot.send_message(chat_id=message.chat.id, text="<b>Время ожидания вышло, номер отменен</b>")
                        raise Exception("time's up")
                    await asyncio.sleep(5)

                auth_account = await urapi.get_access_token_by_code(code=sms_code)
                with open("data/cards.json") as cards_list:
                    cards = json.load(cards_list)
                    card_info = cards["cards"][place % len(cards["cards"])]
                payment_profile = await urapi.get_payment_profile(access_headers=auth_account["access_headers"])
                if len(payment_profile["promoCodes"]) == 0 and len(payment_profile["cards"]) == 0:
                    cloudpayment_card = await urapi.cloudpayments_card(access_headers=auth_account["access_headers"],
                                                                       card_info=card_info,
                                                                       public_id=payment_profile["cloudPaymentsPublicId"])
                    pprint(f'{cloudpayment_card = }')

                    link = await urapi.link_card3ds(data={
                        "payment_url": cloudpayment_card["acsUrl"],
                        "pa_req": cloudpayment_card["paReq"],
                        "md": cloudpayment_card["md"],
                    })
                    CHECK_KEYBOARD = InlineKeyboardMarkup()
                    CHECK_KEYBOARD.add(InlineKeyboardButton(text="Перейти к привязке", web_app=WebAppInfo(url=link["url"])))
                    CHECK_KEYBOARD.add(InlineKeyboardButton(text="Проверить привязку",
                                                            callback_data=f"check-acc_{link['url'].split('=')[1]}_{number['number']}"))
                    await bot.send_message(chat_id=message.chat.id, text="<b>Привязка карты</b>", reply_markup=CHECK_KEYBOARD)

                    # return [f"{number['number']}", auth_account["user_token"]["refresh_token"], 102]
                    cur.execute("INSERT INTO ur_accounts (phone_number, refresh_token, price, user_id, description) VALUES (%s, %s, %s, %s, %s)", (number['number'], auth_account["user_token"]["refresh_token"],
                                                                                                                                                   price, 102, description))
                    conn.commit()
                else:
                    # return [f"{number['number']}", auth_account["user_token"]["refresh_token"], 1]
                    cur.execute("INSERT INTO ur_accounts (phone_number, refresh_token, price, user_id, description) VALUES (%s, %s, %s, %s, %s)", (number['number'], auth_account["user_token"]["refresh_token"],
                                                                                                                                                   price, 1, description))
                    conn.commit()
                    await bot.send_message(chat_id=message.chat.id, text="<b>Аккаунт не прошел валидацию</b>")
            else:
                change_status = await sms.change_number_status(activation_id=number["id"], status="1")
                pprint(change_status)
    except Exception:
        print(traceback.format_exc())
        # return [None, None, None]
    finally:
        print(f"{number['number']} | {auth_account}")


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "check-acc")
async def account_checker(call, state):
    try:
        async with aiohttp.ClientSession() as session:
            cur.execute("SELECT * FROM ur_accounts WHERE phone_number=%s", (call.data.split("_")[2],))
            account_info = cur.fetchall()[0]
            urapi = UrentApi(refresh_token=account_info[1], phone_number=call.data.split("_")[2], session=session)
            access_headers = await urapi.get_access_token()
            check_card = await urapi.check_card3ds(card3ds_id=call.data.split("_")[1])
            post3ds = await urapi.post_3dsecure(access_headers=access_headers, data={
                "md": check_card["content"]["md"],
                "paRes": check_card["content"]["pa_res"]
            })
            if post3ds["errors"]:
                print(post3ds["errors"])
                await call.answer(f'{" ".join(post3ds["errors"][0]["value"])}.', show_alert=True)

            async with state.proxy() as data:
                for promo in data["get_promocodes"]:
                    try:
                        paste_promo = await urapi.post_promocode(access_headers=access_headers, promocode=promo)
                        pprint(f'{paste_promo = }')
                        if data["get_promocodes"].index(promo) + 1 == len(data["get_promocodes"]):
                            break
                        else:
                            await asyncio.sleep(11000)

                    except Exception:
                        print(traceback.format_exc())
            del_card = await urapi.delete_card(access_headers=access_headers)
            pprint(del_card)
            cur.execute("UPDATE ur_accounts SET user_id=%s WHERE phone_number=%s and user_id=102", (0, call.data.split("_")[2]))
            conn.commit()
            await bot.edit_message_text(chat_id=call.message.chat.id, text="<b>Завершено</b>", message_id=call.message.message_id, reply_markup=InlineKeyboardMarkup([[]]))
    except Exception:
        print(traceback.format_exc())


@dp.callback_query_handler(lambda call: call.data == "change-token")
async def process_change_token(call, state: FSMContext):
    CANCEL_KEYBOARD = InlineKeyboardMarkup()
    CANCEL_KEYBOARD.add(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    await Form.get_token.set()
    msg = await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="<b>Пришлите новый токен:</b>", reply_markup=CANCEL_KEYBOARD)
    await state.update_data(cancel_msgID=msg.message_id)


@dp.message_handler(state=Form.get_token)
async def get_new_token(message, state: FSMContext):
    async with state.proxy() as cancel:
        await state.finish()
        await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=cancel["cancel_msgID"],
                                            reply_markup=InlineKeyboardMarkup([[]]))
    if re.compile("[A-Za-z0-9]{32}").match(message.text):
        await bot.send_message(chat_id=message.chat.id, text=f"<b>Токен <code>{message.text}</code> принят</b>")
        cur.execute("UPDATE tokens SET sms_token=%s", (message.text,))
        conn.commit()
    else:
        await bot.send_message(chat_id=message.chat.id, text="<b>Это не похоже на токен</b>")


@dp.message_handler(lambda message: message.text == "Управление пополнениями")
@is_admin
async def managing_refill(message, **kwargs):
    cur.execute('SELECT all_money FROM money')
    await bot.send_message(chat_id=message.chat.id,
                           text=f"<b>За весь период заработано: <code>{cur.fetchall()[0][0]}</code> рублей</b>")


@dp.message_handler(lambda message: message.text == "Управление пользователями")
@is_admin
async def managing_users(message, **kwargs):
    SEARCH_KEYBOARD = InlineKeyboardMarkup()
    SEARCH_KEYBOARD.add(InlineKeyboardButton(text="Инфо. о юзере", callback_data="info-about-user"))
    cur.execute('SELECT user_id FROM users_info')
    await bot.send_message(chat_id=message.chat.id,
                           text=f"<b>Всего пользователей: <code>{len(cur.fetchall())}</code></b>",
                           reply_markup=SEARCH_KEYBOARD)


@dp.callback_query_handler(lambda call: call.data == "info-about-user")
async def info_about_user(call, state: FSMContext):
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        reply_markup=InlineKeyboardMarkup([[]]))
    CANCEL_KEYBOARD = InlineKeyboardMarkup()
    CANCEL_KEYBOARD.add(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    await Form.get_user_id.set()
    msg = await bot.send_message(chat_id=call.message.chat.id, text=f"<b>Пришлите ID пользователя:</b>",
                                 reply_markup=CANCEL_KEYBOARD)
    await state.update_data(cancel_msgID=msg.message_id)


@dp.message_handler(state=Form.get_user_id)
async def get_user_info(message, state: FSMContext):
    try:
        async with state.proxy() as cancel:
            await state.finish()
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=cancel["cancel_msgID"],
                                                reply_markup=InlineKeyboardMarkup([[]]))
        cur.execute("SELECT * FROM users_info WHERE user_id=%s", (message.text,))
        user_info = cur.fetchall()[0]
        EDIT_STAT_USER = InlineKeyboardMarkup()
        EDIT_STAT_USER.add(InlineKeyboardButton(text=f"{'Разбанить' if user_info[5] == 1 else 'Забанить'}",
                                                callback_data=f"{f'unban_{message.text}' if user_info[5] == 1 else f'ban_{message.text}'}"))
        EDIT_STAT_USER.add(InlineKeyboardButton(text="Выдать баланс", callback_data=f"issue-money_{message.text}"),
                           InlineKeyboardButton(text="Забрать баланс", callback_data=f"fetch-money_{message.text}"))
        EDIT_STAT_USER.add(InlineKeyboardButton(text="Выгрузить логи", callback_data=f"get-logs_{message.text}"))
        await bot.send_message(chat_id=message.chat.id, text=f"<b>Информация о пользователе:</b>\n"
                                                             f"<b>ID: <code>{user_info[0]}</code></b>\n"
                                                             f"<b>Баланс: <code>{user_info[1]}</code></b>\n"
                                                             f"<b>Общая сумма пополнений: <code>{user_info[2]}</code></b>\n"
                                                             f"<b>Количество покупок: <code>{user_info[3]}</code></b>\n"
                                                             f"<b>Общая стоимость покупок: <code>{user_info[4]}</code></b>\n"
                                                             f"<b>Бан: <code>{'да' if user_info[5] == 1 else 'нет'}</code></b>",
                               reply_markup=EDIT_STAT_USER)
    except Exception:
        await bot.send_message(chat_id=message.chat.id, text="<b>Не правильный ID пользователя попробуйте еще раз</b>")


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "get-logs")
async def get_logs(call, state: FSMContext):
    files = os.listdir("logs")
    for file in files:
        with open(file=f"logs/{file}", mode="r", encoding="utf-8") as reader:
            with open(file=f"temp/log_{call.data.split('_')[1]}.txt", mode="a", encoding="utf-8") as writer:
                for line in reader:
                    if call.data.split('_')[1] in line:
                        writer.write(line)
    with open(file=f"temp/log_{call.data.split('_')[1]}.txt", mode="rb") as sender:
        await bot.send_document(chat_id=call.message.chat.id, caption=f"<b>Выгрузка логов {call.data.split('_')[1]}</b>", document=sender)
    os.remove(f"temp/log_{call.data.split('_')[1]}.txt")


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "issue-money")
async def issue_money(call, state: FSMContext):
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        reply_markup=InlineKeyboardMarkup([[]]))
    await state.update_data(get_issue_money=f"{call.data.split('_')[1]}")
    CANCEL_KEYBOARD = InlineKeyboardMarkup()
    CANCEL_KEYBOARD.add(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    await Form.get_issue_money.set()
    msg = await bot.send_message(chat_id=call.message.chat.id, text="<b>Сколько денег вы хотите выдать юзеру?</b>",
                                 reply_markup=CANCEL_KEYBOARD)
    await state.update_data(cancel_msgID=msg.message_id)


@dp.message_handler(state=Form.get_issue_money)
async def process_issue_money(message, state: FSMContext):
    try:
        async with state.proxy() as data:
            await state.finish()
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=data["cancel_msgID"],
                                                reply_markup=InlineKeyboardMarkup([[]]))
            cur.execute(
                "UPDATE users_info SET balance= balance + %s, total_balance= total_balance + %s WHERE user_id=%s",
                (int(message.text), int(message.text), data["get_issue_money"]))
            conn.commit()
            await bot.send_message(chat_id=message.chat.id,
                                   text=f"<b>💰 Баланс успешно пополнился на сумму</b> <code>{message.text} ₽</code>")
    except Exception:
        await bot.send_message(chat_id=message.chat.id, text="Что то пошло не так...")
        print(traceback.format_exc())


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "fetch-money")
async def fetch_money(call, state: FSMContext):
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        reply_markup=InlineKeyboardMarkup([[]]))
    await state.update_data(get_fetch_money=f"{call.data.split('_')[1]}")
    CANCEL_KEYBOARD = InlineKeyboardMarkup()
    CANCEL_KEYBOARD.add(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    await Form.get_fetch_money.set()
    msg = await bot.send_message(chat_id=call.message.chat.id, text="<b>Сколько денег вы хотите забрать у юзера?</b>",
                                 reply_markup=CANCEL_KEYBOARD)
    await state.update_data(cancel_msgID=msg.message_id)


@dp.message_handler(state=Form.get_fetch_money)
async def process_issue_money(message, state: FSMContext):
    try:
        async with state.proxy() as data:
            await state.finish()
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=data["cancel_msgID"],
                                                reply_markup=InlineKeyboardMarkup([[]]))
            cur.execute(
                "UPDATE users_info SET balance= balance - %s, total_balance= total_balance - %s WHERE user_id=%s",
                (int(message.text), int(message.text), data["get_fetch_money"]))
            conn.commit()
            await bot.send_message(chat_id=message.chat.id, text="<b>Успешно забрано</b>")
    except Exception:
        await bot.send_message(chat_id=message.chat.id, text="Что то пошло не так...")
        print(traceback.format_exc())


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "ban")
async def ban_user(call):
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        reply_markup=InlineKeyboardMarkup([[]]))
    cur.execute("UPDATE users_info SET ban_status=%s WHERE user_id=%s", (1, call.data.split("_")[1],))
    conn.commit()
    await bot.send_message(chat_id=call.message.chat.id, text="<b>Успешно забанен</b>")


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "unban")
async def unban_user(call):
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        reply_markup=InlineKeyboardMarkup([[]]))
    cur.execute("UPDATE users_info SET ban_status=%s WHERE user_id=%s", (0, call.data.split("_")[1],))
    conn.commit()
    await bot.send_message(chat_id=call.message.chat.id, text="<b>Успешно разбанен</b>")


@dp.message_handler(lambda message: message.text == "Управление промокодами")
@is_admin
async def managing_promo_codes(message, **kwargs):
    SELECT_METHOD_KEYBOARD = InlineKeyboardMarkup()
    SELECT_METHOD_KEYBOARD.add(InlineKeyboardButton(text="Статистика промокода", callback_data="promo-info"))
    SELECT_METHOD_KEYBOARD.add(InlineKeyboardButton(text="Вручную", callback_data="create-promo_handmade"),
                               InlineKeyboardButton(text="Автоматически", callback_data="create-promo_auto"))

    await bot.send_message(chat_id=message.chat.id, text="<b>Управление промокодами</b>",
                           reply_markup=SELECT_METHOD_KEYBOARD)


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "promo-info")
async def process_get_info(call, state: FSMContext):
    CANCEL_KEYBOARD = InlineKeyboardMarkup()
    CANCEL_KEYBOARD.add(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        reply_markup=InlineKeyboardMarkup([[]]))
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await Form.info_promocode.set()
    msg = await bot.send_message(chat_id=call.message.chat.id,
                                 text="<b>Введите промокод для получения статистики о нем</b>",
                                 reply_markup=CANCEL_KEYBOARD)
    await state.update_data(cancel_msgID=msg.message_id)


@dp.message_handler(state=Form.info_promocode)
async def get_promo_info(message, state: FSMContext):
    try:
        async with state.proxy() as cancel:
            await state.finish()
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=cancel["cancel_msgID"],
                                                reply_markup=InlineKeyboardMarkup([[]]))

        cur.execute("SELECT * FROM promocodes WHERE name=%s", (message.text,))
        promo_info = cur.fetchall()[0]
        await bot.send_message(chat_id=message.chat.id, text=f"<b>Промокод <code>{promo_info[0]}</code></b>\n"
                                                             f"<b>Осталось использований <code>{promo_info[1]}</code> шт.</b>\n"
                                                             f"<b>Номинал <code>{promo_info[2]}</code> руб.</b>")
    except Exception:
        await bot.send_message(chat_id=message.chat.id,
                               text="<b>Промокод не найден, проверьте правильность написанного "
                                    "промокода или он был полностью использован и удален</b>")
        print(traceback.format_exc())


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "create-promo")
async def process_create_promocodes(call, state: FSMContext):
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        reply_markup=InlineKeyboardMarkup([[]]))
    CANCEL_KEYBOARD = InlineKeyboardMarkup()
    CANCEL_KEYBOARD.add(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    if call.data.split("_")[1] == "handmade":
        await Form.name_of_promo.set()
        msg = await bot.send_message(chat_id=call.message.chat.id, text="<b>Введите название промокода:</b>",
                                     reply_markup=CANCEL_KEYBOARD)
        await state.update_data(cancel_msgID=msg.message_id)
    elif call.data.split("_")[1] == "auto":
        await Form.count_promocodes.set()
        msg = await bot.send_message(chat_id=call.message.chat.id, text="<b>Введите количество промокодов:</b>",
                                     reply_markup=CANCEL_KEYBOARD)
        await state.update_data(cancel_msgID=msg.message_id)


@dp.message_handler(state=Form.count_promocodes)
async def get_count_promocodes(message, state: FSMContext):
    try:
        async with state.proxy() as cancel:
            await state.finish()
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=cancel["cancel_msgID"],
                                                reply_markup=InlineKeyboardMarkup([[]]))

        codes = [str(uuid.uuid4().hex) for _ in range(int(message.text))]
        for code in codes:
            cur.execute("INSERT INTO promocodes (name, number_of_uses, price, used_ids) VALUES (%s, %s, %s, %s)",
                        (code, 1, randint(5, 15), {"ids": [], }))
        conn.commit()
        codes_text = "\n".join(codes)
        if len(codes) <= 100:
            await bot.send_message(chat_id=message.chat.id, text=f"Были созданы промокоды:\n"
                                                                 f"{codes_text}")
        else:
            with open('data/promocodes.txt', 'w') as file:
                file.write(codes_text)
            await bot.send_document(chat_id=message.chat.id, document=open("data/promocodes.txt", "rb"),
                                    caption="Список промокодов:", reply_markup=ADMIN_KEYBOARD)
    except Exception:
        await bot.send_message(chat_id=message.chat.id, text="Что то пошло не так попробуйте еще раз")
        print(traceback.format_exc())


@dp.message_handler(state=Form.name_of_promo)
async def get_name_promo(message, state: FSMContext):
    async with state.proxy() as cancel:
        await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=cancel["cancel_msgID"],
                                            reply_markup=InlineKeyboardMarkup([[]]))
    CANCEL_KEYBOARD = InlineKeyboardMarkup()
    CANCEL_KEYBOARD.add(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    await state.update_data(name_of_promo=message.text)
    await Form.number_of_uses.set()
    msg = await bot.send_message(chat_id=message.chat.id, text="Введите максимальное количество использований:",
                                 reply_markup=CANCEL_KEYBOARD)
    await state.update_data(cancel_msgID=msg.message_id)


@dp.message_handler(state=Form.number_of_uses)
async def get_number_of_uses_promo(message, state: FSMContext):
    try:
        async with state.proxy() as cancel:
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=cancel["cancel_msgID"],
                                                reply_markup=InlineKeyboardMarkup([[]]))
        CANCEL_KEYBOARD = InlineKeyboardMarkup()
        CANCEL_KEYBOARD.add(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
        await state.update_data(number_of_uses=int(message.text))
        await Form.price_of_promo.set()
        msg = await bot.send_message(chat_id=message.chat.id, text="Введите номинал промокода:",
                                     reply_markup=CANCEL_KEYBOARD)
        await state.update_data(cancel_msgID=msg.message_id)
    except Exception:
        await bot.send_message(chat_id=message.chat.id, text="Что то пошло не так попробуйте еще раз")
        print(traceback.format_exc())


@dp.message_handler(state=Form.price_of_promo)
async def get_price_promo(message, state: FSMContext):
    try:
        async with state.proxy() as data:
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=data["cancel_msgID"],
                                                reply_markup=InlineKeyboardMarkup([[]]))
            cur.execute("INSERT INTO promocodes (name, number_of_uses, price, used_ids) VALUES (%s, %s, %s, %s)",
                        (data["name_of_promo"], data["number_of_uses"], int(message.text), json.dumps({"ids": []})))
            conn.commit()
            await bot.send_message(chat_id=message.chat.id, text=f"Был создан промокод:\n"
                                                                 f"Название: {data['name_of_promo']}\n"
                                                                 f"Максимальное количество использований: {data['number_of_uses']}\n"
                                                                 f"Номиналом: {int(message.text)}")
        await state.finish()
    except Exception:
        await bot.send_message(chat_id=message.chat.id, text="Что то пошло не так попробуйте еще раз")
        print(traceback.format_exc())


@dp.message_handler(lambda message: message.text == "Рассылка")
@is_admin
async def get_text_to_mailing(message, state: FSMContext, **kwargs):
    CANCEL_KEYBOARD = InlineKeyboardMarkup()
    CANCEL_KEYBOARD.add(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    await Form.mailing_msg.set()
    msg = await bot.send_message(chat_id=message.chat.id, text="<b>Пришлите сообщение для рассылки:</b>",
                                 reply_markup=CANCEL_KEYBOARD)
    await state.update_data(cancel_msgID=msg.message_id)


@dp.message_handler(state=Form.mailing_msg, content_types=["any"])
async def run_mailing(message, state: FSMContext):
    async with state.proxy() as cancel:
        await state.finish()
        await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=cancel["cancel_msgID"],
                                            reply_markup=InlineKeyboardMarkup([[]]))

    await bot.send_message(chat_id=message.chat.id, text="<b>Рассылка началась</b>", reply_markup=ADMIN_KEYBOARD)
    cur.execute("SELECT user_id FROM users_info")
    users = cur.fetchall()
    list_of_not_received_msg_users = []
    for user in users:
        try:
            await bot.copy_message(chat_id=user[0], from_chat_id=message.chat.id, message_id=message.message_id)
        except Exception:
            list_of_not_received_msg_users.append(user[0])
    await bot.send_message(chat_id=message.chat.id, text=f"<b>Рассылка прошла успешно\n"
                                                         f"Всего пользователей <code>{len(users)}</code>\n"
                                                         f"Cообщения пришли <code>{len(users) - len(list_of_not_received_msg_users)}</code> пользователям</b>")
