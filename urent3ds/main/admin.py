from django.contrib import admin

from main.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    pass
