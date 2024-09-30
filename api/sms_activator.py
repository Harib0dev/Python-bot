import asyncio
import traceback
import uuid
import aiohttp
from loader import *
import secrets
import string
from pprint import pprint
import json


class SMSActivator(object):
    def __init__(self, key=None, session=None):
        self.key = key
        self.session = session
        self.url = "https://sms-acktiwator.ru/api/"

    async def get_balance(self):
        async with self.session.get(url=f"{self.url}getbalance/{self.key}") as balance:
            return float(await balance.text())

    async def get_number(self):
        async with self.session.get(url=f"{self.url}getnumber/{self.key}?id=534&code=RU") as number:
            return await number.json()

    async def get_active_activation(self, nid):
        async with self.session.get(url=f"{self.url}getlatestcode/{self.key}?id={nid}") as number:
            return await number.text()

    async def change_number_status(self, activation_id, status):
        async with self.session.get(url=f"{self.url}setstatus/{self.key}?id={activation_id}&status={status}") as number:
            return await number.text()

