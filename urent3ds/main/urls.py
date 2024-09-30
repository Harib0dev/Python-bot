from django.urls import path
from main import views


urlpatterns = [
    path('payment/create/', views.CreatePaymentLink.as_view()),
    path('payment/view/', views.PaymentView.as_view()),
    path("check/payment/", views.CheckPayment.as_view()),
]