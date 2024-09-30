
import ssl


import requests


def get_cloudpayments(url, md, pareq):
    data = {
        "PaReq": pareq,
        "MD": str(md),
        "TermUrl": ""
    }
    return requests.post(url, data=data, verify=ssl.VERIFY_DEFAULT)

# https://demo.cloudpayments.ru/WebFormPost/GetWebViewData