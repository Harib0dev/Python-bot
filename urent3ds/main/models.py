from django.db import models
from urent_3ds.settings import DOMAIN


class TimedBaseModel(models.Model):
    """Базовая модель содержащая нужные поля"""

    class Meta:
        abstract = True

    id = models.AutoField(primary_key=True, verbose_name='Id колонки')
    created_at = models.DateTimeField(auto_now_add=True)


class Payment(TimedBaseModel):
    CHOISER_TYPE = (
        (1, "mirconnect"),
        (2, "cloudpayment")
    )
    payment_url = models.CharField(verbose_name="Url Send", max_length=10000)
    pa_req = models.TextField(verbose_name="Токен", max_length=10000)
    md = models.CharField(verbose_name="мд", max_length=1000)
    special_id = models.CharField(verbose_name="Special Id", max_length=1000)
    server_type = models.IntegerField(choices=CHOISER_TYPE)
    other = models.TextField(max_length=100000, null=True, blank=True)
    url = models.SlugField(unique=True, verbose_name="Ссыль", max_length=1000)

    def get_absolute_url(self):
        return f"{DOMAIN}" + "urent/payment/view/?url=" + self.url
