import asyncio
import traceback
import uuid
import aiohttp
from loader import *
import secrets
import string
from pprint import pprint
import json
from uuid import uuid4


class LolzTeam(object):
    def __init__(self, token=None, session=None):
        self.user_id = None
        self.username = None
        self.token = token
        self.session = session
        self.url = "https://api.zelenka.guru/"
        self.headers = {
            'Authorization': f'Bearer {token}'
        }
        self.last_request = {}

    async def get_me(self):
        try:
            async with self.session.get(url="https://api.lzt.market/me", headers=self.headers) as me:
                self.username = (await me.json())["user"]['username']
                self.user_id = (await me.json())["user"]['user_id']
                print(self.username)
                return await me.json()
        except Exception:
            await asyncio.sleep(1)
            await self.get_me()

    async def get_link(self, amount: int, comment: str):
        return f'https://lzt.market/balance/transfer?username={self.username}&hold=0&amount={amount}&comment={comment}'

    async def check_payments(self, comment):
        try:
            return [item for item in self.last_request.values()
                    if item["data"] is not False
                    and "comment" in item["data"]
                    and item["data"]["comment"] == comment]
        except Exception:
            return []

    async def get_payments(self):
        try:
            async with self.session.get(url=f'{self.url}market/user/{self.user_id}/payments', headers=self.headers,
                                        params={"type": "income", }) as payments:
                if payments.status == 200:
                    self.last_request = (await payments.json())['payments']
                else:
                    return {"error": f"{(await payments.text()).split('<h1>')[1].split('</h1>')[0]}"}

        except Exception:
            print(f"---------LOLZ---------\n"
                  f"{traceback.format_exc()}")