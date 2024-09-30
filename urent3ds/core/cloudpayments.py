import ssl

import jwt
import uuid

import requests


class CloudPayModule:
    def __init__(self):
        self.token_verification = None

    def generate_token(self, server_id):
        headers = {
          "threeDSServerTransID": server_id,
          "acsTransID": str(uuid.uuid4()),
          "messageType": "CRes",
          "messageVersion": "2.1.0",
          "transStatus": "Y"
        }
        result_jwt = jwt.encode(headers=headers, payload={}, algorithm="HS256", key="")
        self.token_verification = result_jwt
        return result_jwt.split(".")[0]

    @staticmethod
    def get_redirect_url(url, pa_req, md):
        data = {
            "PaReq": pa_req,
            "MD": md,
            "TermUrl": ""
        }
        headers = {
            "User-Agent": "%D0%AE%D1%80%D0%B5%D0%BD%D1%82/3 CFNetwork/1240.0.4 Darwin/20.6.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Language": "ru",
            "Accept-Encoding": "gzip, deflate, br"
        }
        response = requests.post(url=url, data=data, headers=headers, verify=ssl.VERIFY_DEFAULT)
        if response.status_code == 200 and "ThreeDsServerTransId" in response.url:
            uuid_parameter_id = response.url.split("ThreeDsServerTransId=")[1].split("&")[0]
            return [response.url, uuid_parameter_id]
        else:
            return [False]
