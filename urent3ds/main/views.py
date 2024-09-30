from django.shortcuts import render, redirect
from django.views import View
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.cloudpayments import CloudPayModule
from core.mirconnect import MirconnectModule
from . import serializers
from core import requests as req
from .models import Payment


class CreatePaymentLink(APIView):
    def post(self, request):
        serializer = serializers.CreateUrlSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = serializer.validated_data["payment_url"]
        pa_req = serializer.validated_data["pa_req"]
        md = serializer.validated_data["md"]
        other_data = None
        if "mirconnect" in url:
            server_type = 1
            module = MirconnectModule()
            response_content = module.get_html_form(url, pa_req, md)
            if not response_content[0]:
                return Response(
                    {
                        "status": False,
                        "message": "fail create payment url"
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            other_data = response_content[1].text
            secret_token = response_content[1].cookies.get_dict()["JSESSIONID"]
        else:
            module = CloudPayModule()
            response_content = module.get_redirect_url(url, pa_req, md)
            if not response_content[0]:
                return Response(
                    {
                    "status": False,
                    "message": "fail create payment url"
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            server_type = 2
            secret_token = response_content[1]
        payment_data = serializer.save(special_id=secret_token, server_type=server_type, other=other_data)
        return Response(
            {
                "status": True,
                "url": payment_data.get_absolute_url()
            }
        )


class PaymentView(View):
    def get(self, request):
        url = request.GET.get("url")
        if url is None:
            return Response("Not view data")
        payment = Payment.objects.filter(url=url)
        if payment.first() is None:
            return Response("Not view data")
        payment = payment.first()
        if "mirconnect" in payment.payment_url:
            return render(request, "index.html", context={"template": payment.other})
        else:
            response = req.get_cloudpayments(payment.payment_url, payment.md, payment.pa_req)
            if response.status_code == 200:
                return redirect(response.url)
            else:
                return Response("fail create payment url")


class CheckPayment(APIView):
    def get(self, request):
        url = request.GET.get("url")
        if not url:
            return Response(
                {
                    "status": False,
                    "message": "not found url"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        payment = Payment.objects.filter(url=url)
        if payment is None:
            return Response(
                {
                    "status": False,
                    "message": "not found url"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        payment = payment.first()
        if payment.server_type == 1:
            module = MirconnectModule()
            path_pay = payment.payment_url.split("/", 4)[3]
            response_content = module.get_check_payment(payment.special_id, path_pay)
            if not response_content[0]:
                return Response(
                    {
                        "status": False,
                        "message": "Error when get unique key for check payment"
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            pa_res = response_content[1]
            md = response_content[2]
        else:
            module = CloudPayModule()
            jwt_token = module.generate_token(payment.special_id)
            pa_res = jwt_token
            md = payment.md
        return Response(
            {
                "status": True,
                "content": {
                    "pa_res": pa_res,
                    "md": md
                }
            }
        )