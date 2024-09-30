from loader import dp, bot, conn, cur, p2p
from data.config import *
import json
import traceback


def is_admin(func):
    async def wrapper(*args, **kwargs):
        try:
            with open("data/admins.json", "rb") as file:
                if args[0].from_user.id in json.load(file)["admins"]:
                    return await func(*args, **kwargs)

        except Exception:
            print(traceback.format_exc())

    return wrapper


def is_baned(func):
    async def wrapper(*args, **kwargs):
        try:
            cur.execute("SELECT ban_status FROM users_info WHERE user_id=%s", (args[0].from_user.id,))
            stat = cur.fetchall()
            if stat == [] or stat[0][0] == 0:
                return await func(*args, **kwargs)
            else:
                return await bot.send_message(chat_id=args[0].from_user.id, text="<b>⛔ Вы были заблокированы в боте </b>")
        except Exception:
            print(traceback.format_exc())

    return wrapper