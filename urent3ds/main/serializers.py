from rest_framework import serializers
from main.models import Payment
import uuid


class CreateUrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("payment_url", "pa_req", "md")

    def save(self, **kwargs):
        url_link = str(uuid.uuid4())
        return Payment.objects.create(
            payment_url=self.validated_data["payment_url"],
            pa_req=self.validated_data["pa_req"],
            md=self.validated_data["md"],
            url=url_link,
            **kwargs
        )
