import traceback
import uuid
import aiohttp
from data.config import CLIENT_SECRET
from loader import *
import secrets
import string
from pprint import pprint
from random import randint, choice
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from base64 import b64encode, b64decode, urlsafe_b64encode


class UrentApi(object):
    def __init__(self, refresh_token=None, phone_number=None, session=None):
        self.headers = {
            "accept-encoding": "gzip",
            "accept-language": "ru-RU",
            "user-agent": f"Urent/1.13 (ru.urentbike.app; build: 1120; Android {randint(5, 10)}.{randint(0, 10)}.{randint(0, 10)}) okhttp/4.9.1",
            'ur-platform': 'Android',
            'ur-session': str(uuid.uuid4()),
            'ur-device-id': ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(15)),
            'ur-version': '1.13',
        }
        self.refresh_token = refresh_token
        self.phone_number = phone_number
        self.session = session

        self.access_headers = {}

    async def get_access_token(self):
        data_access_token = {
            "client_id": "mobile.client.android",
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "scope": "bike.api ordering.api location.api customers.api payment.api maintenance.api notification.api "
                     "log.api ordering.scooter.api driver.bike.lock.offo.api driver.scooter.ninebot.api identity.api "
                     "offline_access",
            "refresh_token": self.refresh_token
        }

        async with self.session.post(url='https://service.urentbike.ru/gatewayclient/api/v1/connect/token',
                                     headers=self.headers, data=data_access_token) as response_connect_token:
            account_session = await response_connect_token.json()
            cur.execute("UPDATE ur_accounts SET refresh_token=%s WHERE phone_number=%s", (account_session["refresh_token"], self.phone_number, ))
            conn.commit()
        self.access_headers = {**self.headers, **{"authorization": f'Bearer {account_session["access_token"]}'}}
        return {**self.headers, **{"authorization": f'Bearer {account_session["access_token"]}'}}

    async def get_payment_profile(self, access_headers=None):
        async with self.session.get(url="https://service.urentbike.ru/gatewayclient/api/v1/payment/profile",
                                    headers=(access_headers or self.access_headers)) as response_payment_profile:
            return await response_payment_profile.json()

    async def get_activity(self, access_headers=None):
        async with self.session.get(url="https://service.urentbike.ru/gatewayclient/api/v2/activity",
                               headers=(access_headers or self.access_headers)) as response_activity:
            return await response_activity.json()

    async def get_scooter_info(self, scooter_id, access_headers=None):
        async with self.session.get(url=f"https://service.urentbike.ru/gatewayclient/api/v3/transports/S.{scooter_id}",
                                    headers=(access_headers or self.access_headers)) as response_scooter_info:
            return await response_scooter_info.json()

    async def get_urent_profile(self, access_headers=None):
        async with self.session.get(url="https://service.urentbike.ru/gatewayclient/api/v1/profile",
                               headers=(access_headers or self.access_headers)) as response_profile:
            return await response_profile.json()

    async def order_make(self, data, access_headers=None):
        async with self.session.post(url="https://service.urentbike.ru/gatewayclient/api/v1/order/make",
                                     headers=(access_headers or self.access_headers), json=data) as response_order_make:
            return await response_order_make.json()

    async def order_end(self, data, access_headers=None):
        async with self.session.post(url="https://service.urentbike.ru/gatewayclient/api/v1/order/end",
                                     headers=(access_headers or self.access_headers), json=data) as response_order_end:
            return await response_order_end.json()

    async def order_wait(self, data, access_headers=None):
        async with self.session.post(url="https://service.urentbike.ru/gatewayclient/api/v1/order/wait",
                                     headers=(access_headers or self.access_headers), json=data) as response_order_wait:
            return await response_order_wait.json()

    async def order_resume(self, data, access_headers=None):
        async with self.session.post(url="https://service.urentbike.ru/gatewayclient/api/v1/order/resume",
                                     headers=(access_headers or self.access_headers), json=data) as response_order_resume:
            return await response_order_resume.json()

    async def delete_card(self, access_headers=None):
        payment_activity = await self.get_payment_profile((access_headers or self.access_headers))
        async with self.session.delete(url=f"https://service.urentbike.ru/gatewayclient/api/v1/cards/cards/{payment_activity['cards'][0]['id']}",
                                       headers=(access_headers or self.access_headers)) as response_delete_card:
            return await response_delete_card.json()

    async def delete_account(self, access_headers=None):
        async with self.session.delete(url="https://service.urentbike.ru/gatewayclient/api/v1/deletemy",
                                       headers=(access_headers or self.access_headers)) as response_delete_account:
            return await response_delete_account.json()

    async def post_promocode(self, promocode, access_headers=None):
        async with self.session.post(url="https://service.urentbike.ru/gatewayclient/api/v1/profile/promocode", headers=(access_headers or self.access_headers),
                                json={"promoCode": promocode}) as response_promocode:
            return await response_promocode.json()

    # --------------------------------------- auto registration part ---------------------------------------

    async def get_public_key(self):

        data_public_token = {
            "client_id": "mobile.client.android",
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials",
            "scope": "bike.api ordering.api location.api customers.api payment.api maintenance.api ordering.scooter.api"
        }

        async with self.session.post(url='https://service.urentbike.ru/gatewayclient/api/v1/connect/token',
                                headers=self.headers, data=data_public_token) as response_public_token:
            public_token = await response_public_token.json()
            return {**self.headers, **{"authorization": f'Bearer {public_token["access_token"]}'}}

    async def get_mobile_code(self, access_headers):

        data_get_code = {
            "osVersion": f"{randint(5, 10)}.{randint(0, 10)}.{randint(0, 10)}",
            "uniqueId": self.headers['ur-device-id'],
            "phoneModel": f"{choice(('Xiaomi redmi note', 'iphone', 'samsung'))} {randint(6, 11)}{choice((' PRO', ''))}",
            "phoneNumber": self.phone_number,
            "phoneCountryCode": "ru"
        }

        async with self.session.post(url="https://service.urentbike.ru/gatewayclient/api/v1/mobile/code",
                                headers=(access_headers or self.access_headers), json=data_get_code) as response_get_code:
            return await response_get_code.json()

    async def get_access_token_by_code(self, code):

        data_get_user_token = {
            "client_id": "mobile.client.android",
            "client_secret": CLIENT_SECRET,
            "username": self.phone_number,
            "password": code,
            "scope": "bike.api ordering.api location.api customers.api payment.api maintenance.api notification.api log.api ordering.scooter.api driver.bike.lock.offo.api driver.scooter.ninebot.api identity.api offline_access",
            "grant_type": "password",
        }

        async with self.session.post(url="https://service.urentbike.ru/gatewayclient/api/v1/connect/token",
                                headers=self.headers, data=data_get_user_token) as response_user_token:
            return {"user_token": await response_user_token.json(),
                    "access_headers": {**self.headers, **{"authorization": f'Bearer {(await response_user_token.json())["access_token"]}'}}}

    # --------------------------------------- link card part ---------------------------------------

    async def cloudpayments_card(self, access_headers, card_info: dict, public_id):
        encryptor = RSA.import_key(b64decode(UR_PUBLIC_KEY))
        cipher_rsa = PKCS1_v1_5.new(encryptor)
        encrypted = b64encode(cipher_rsa.encrypt(f"{card_info['card_number']}@{card_info['exp']}@{card_info['cvv']}@{public_id}".encode()))
        data = {
            "cardCryptogramPacket": f"01{card_info['card_number'][0:6]}{card_info['card_number'][12:16]}{card_info['exp']}04{encrypted.decode('utf-8')}",
            "cardHolder": ""
        }
        async with self.session.post(url="https://service.urentbike.ru/gatewayclient/api/v1/cloudpayments/card",
                                headers=(access_headers or self.access_headers), json=data) as response_cloudpayment:
            cryprogram_ans = await response_cloudpayment.json()
        headers_payment_acs = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip,deflate',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'connection': 'keep-alive',
            'content-type': 'application/x-www-form-urlencoded',
            'host': 'api.cloudpayments.ru',
            'origin': 'null',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0(Linux;Android7.1.2;SM-G955NBuild/NRD90M.G955NKSU1AQDC;wv)AppleWebKit/537.36(KHTML,like Gecko) Version/4.0 Chrome/92.0.4515.131 Mobile Safari/537.36',
            'x-requested-with': 'ru.urentbike.app'
        }
        data_payment_acs = {
            "PaReq": cryprogram_ans['paReq'],
            "MD": cryprogram_ans['md'],
            "TermUrl": "https://demo.cloudpayments.ru/WebFormPost/GetWebViewData",
        }
        async with self.session.post(url=cryprogram_ans["acsUrl"], headers=headers_payment_acs, data=data_payment_acs,
                                     allow_redirects=False) as not_used_ans:
            return cryprogram_ans

    async def set_browser_info(self, cryptogram):
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'connection': 'keep-alive',
            'content-type': 'application/json',
            'host': 'api.cloudpayments.ru',
            'origin': 'https://3ds.cloudpayments.ru',
            'referer': 'https://3ds.cloudpayments.ru/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0(Linux;Android 7.1.2; SM-G955N Build/NRD90M.G955NKSU1AQDC;wv) AppleWebKit/537.36(KHTML, like Gecko) '
                          'Version/4.0 Chrome/Mobile Safari/537.36',
            'x-request-id': f'{cryptogram["md"]}@{cryptogram["paReq"].split("@")[0]}',
            'x-requested-with': 'ru.urentbike.app'
        }
        data = {
            "JavaEnabled": 'false',
            "JavaScriptEnabled": 'true',
            "Language": "ru-RU",
            "UserAgent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G955N Build/NRD90M.G955NKSU1AQDC; wv) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Version/4.0 Chrome/Mobile Safari/537.36",
            "TimeZone": "-120",
            "Height": 800,
            "Width": 450,
            "ColorDepth": 24,
            "TransactionId": cryptogram["md"],
            "ThreeDsCallbackId": cryptogram["paReq"].split("@")[0]
        }
        async with self.session.post(url="https://api.cloudpayments.ru/payment/setBrowserInfo", headers=headers,
                                     json=data) as set_browser_info:
            return await set_browser_info.json()

    async def post_3dsecure(self, access_headers, cryptogram=None, data=None):
        if data != None:
            data_post3ds = data
        else:
            data_post3ds = {
            "md": cryptogram["md"],
            "paRes": "ZnJpY3Rpb25sZXNz=="
            }
        async with self.session.post(url="https://service.urentbike.ru/gatewayclient/api/v1/cloudpayments/post3ds",
                                     headers=(access_headers or self.access_headers), json=data_post3ds) as post3ds:
            return await post3ds.json()

    async def link_card3ds(self, data: dict):
        async with self.session.post(url="https://ДОМЕННОЕ ИМЯ/urent/payment/create/", json=data, verify_ssl=False) as linker:
            return await linker.json()

    async def check_card3ds(self, card3ds_id):
        async with self.session.get(url=f"https://ДОМЕННОЕ ИМЯ/urent/check/payment/?url={card3ds_id}", verify_ssl=False) as link_info:
            return await link_info.json()