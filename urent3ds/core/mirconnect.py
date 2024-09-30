import ssl

import requests
from bs4 import BeautifulSoup as soup


class MirconnectModule:
    @staticmethod
    def get_html_form(url, pa_req, md):
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
        if response.status_code == 200:
            return [True, response]
        else:
            return [False]

    def get_check_payment(self, session_id, path):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://3ds-ds2.mirconnect.ru",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
            "Referer": f"https://3ds-ds2.mirconnect.ru/{path}/authres;mdsessionid={session_id}"
        }
        data = {
            "mdsessionid": session_id
        }
        response = requests.post(f"https://3ds-ds2.mirconnect.ru/{path}/paresforward;", data=data, headers=headers, verify=ssl.VERIFY_DEFAULT)
        if response.status_code != 200:
            return [False]
        else:
            parsed_html = soup(response.content, 'html.parser')
            pa_res = parsed_html.find("input", {"name": "PaRes"}).get("value")
            md = parsed_html.find("input", {"name": "MD"}).get("value")
            if pa_res is None:
                return [False]
            return [True, pa_res, md]
