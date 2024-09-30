import traceback
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils import executor
import time
from loader import *
import re
from numpy import arange
from pprint import pprint
from uuid import uuid4
import json
import pickle

package = {}


class Paginator(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Paginator, cls).__new__(cls)
        return cls.instance

    @staticmethod
    def importer():
        global package
        try:
            with open("data/paginations.pkl", "rb") as fp:
                package = pickle.load(fp)
        except Exception:
            print(traceback.format_exc())
            package = {}

    @staticmethod
    async def adder(user_id, item_id, array):
        global package
        if user_id not in package.keys():
            package[user_id] = {item_id: array}
        else:
            package[user_id].update({item_id: array})

    @staticmethod
    async def remover(user_id, item_id):
        global package
        package[user_id].pop(item_id)

    @staticmethod
    async def getter(user_id, item_id):
        global package
        return package[user_id][item_id] if item_id in package[user_id].keys() else None

    @staticmethod
    def exporter():
        global package
        try:
            with open("data/paginations.pkl", "wb") as fp:
                pickle.dump(package, fp)
        except Exception:
            print(traceback.format_exc())


async def paginator(msg_id, user_id, add_down=InlineKeyboardMarkup(), add_up=InlineKeyboardMarkup(),
                    old_keyboard=(), page=1, array=None, row=2, call_data="", spliter="|"):
    try:
        keyboard = InlineKeyboardMarkup(row_width=row, )
        pagin = Paginator()

        await pagin.adder(user_id=user_id, item_id=msg_id, array={
            "add_up": add_up,
            "pages": array,
            "add_down": add_down,
            "call_data": call_data,
            "spliter": spliter
        })
        if len(array) > page - 1 >= 0:

            for item in add_up['inline_keyboard']:
                keyboard["inline_keyboard"].append(item)

            keyboard.add(*[InlineKeyboardButton(text=item, callback_data=f"{call_data}{spliter}{item}") for item in array[page - 1]])
            keyboard.row(InlineKeyboardButton(text="⬅️", callback_data=f"page_back_{msg_id}"),
                         InlineKeyboardButton(text=f"{page}", callback_data=f"page_now_{msg_id}"),
                         InlineKeyboardButton(text="➡️", callback_data=f"page_next_{msg_id}"))

            for item in add_down['inline_keyboard']:
                keyboard["inline_keyboard"].append(item)

            return keyboard
        else:
            raise Exception
    except Exception:
        print(traceback.format_exc())
        return old_keyboard


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == 'page')  # needed tests
async def processor_pagination(call, state: FSMContext):
    try:
        pagin = Paginator()
        data = await pagin.getter(user_id=str(call.message.chat.id), item_id=call.data.split("_")[2])
        number = 0
        msg_id = call.data.split("_")[2]
        for number, package in enumerate(call.message.reply_markup.inline_keyboard):
            if len(package) == 3 and package[0]["callback_data"].split("_")[0] == "page"\
                                 and package[1]["callback_data"].split("_")[0] == "page"\
                                 and package[2]["callback_data"].split("_")[0] == "page":
                break
        if call.data.split("_")[1] == "back":
            await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                reply_markup=(await paginator(page=int(call.message.reply_markup.inline_keyboard[number][1]["text"]) - 1 if 0 < int(call.message.reply_markup.inline_keyboard[number][1]["text"]) - 1 else len(data["pages"]),
                                                                              old_keyboard=call.message.reply_markup.inline_keyboard,
                                                                              msg_id=msg_id,
                                                                              user_id=str(call.message.chat.id),
                                                                              add_up=data["add_up"],
                                                                              add_down=data["add_down"],
                                                                              array=data["pages"],
                                                                              call_data=data["call_data"],
                                                                              spliter=data["spliter"])))

        elif call.data.split("_")[1] == "next":
            await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                reply_markup=(await paginator(page=int(call.message.reply_markup.inline_keyboard[number][1]["text"]) + 1 if len(data['pages']) >= int(call.message.reply_markup.inline_keyboard[number][1]["text"]) + 1 else 1,
                                                                              old_keyboard=call.message.reply_markup.inline_keyboard,
                                                                              msg_id=msg_id,
                                                                              user_id=str(call.message.chat.id),
                                                                              add_up=data["add_up"],
                                                                              add_down=data["add_down"],
                                                                              array=data["pages"],
                                                                              call_data=data["call_data"],
                                                                              spliter=data["spliter"])))
        elif call.data.split("_")[1] == "now":
            await call.answer(f"Вы находитесь на странице {call.message.reply_markup.inline_keyboard[number][1]['text']}", show_alert=True)

    except Exception:
        print(traceback.format_exc())
        return 0
