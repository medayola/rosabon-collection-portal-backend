import datetime

from django.conf import settings
from django.db import transaction
from rest_framework import serializers

from mandates.models import Mandate, Rental
from payment.transaction import PaystackTransaction
from pipeline.models import MandateReview, PaymentDetail


class PaystackSerializer(serializers.Serializer):
    reference = serializers.CharField(max_length=200)
    trxref = serializers.CharField(max_length=200)

    def validate_reference_code(self, reference):
        try:
            __transaction__ = PaystackTransaction(
                authorization_key=settings.PAYSTACK_AUTHORIZATION_KEY)
            __status__, __is_valid__, _, __verification__ = __transaction__.verify(
                reference=reference
            )
        except Exception:
            return None

        # update the mandate with the status
        if __is_valid__ is True and __status__ == 200:
            try:
                with transaction.atomic():
                    __ref__ = self.data['reference']
                    __auth__ = __verification__['authorization']

                    __mandate_review__ = MandateReview.objects.filter(
                        code__iexact=__ref__).first()

                    if __mandate_review__:
                        __mandate_review__.authorization_code = __auth__[
                            'authorization_code']

                        __mandate_review__.foward()
                        __mandate_review__.save()

                        __mandate__ = __mandate_review__.mandate
                        __mandate__.authorization_code = __auth__[
                            'authorization_code']
                        __mandate__.save()

                        __customer__ = __mandate__.customer
                        __customer__.paystack_email = __verification__[
                            'customer']['email']
                        __customer__.save()

                        # create a payment detail
                        try:
                            exp_year = int(__auth__['exp_year'])
                            exp_month = int(__auth__['exp_month'])
                            expiry_date = datetime.date(exp_year, exp_month, 1)
                        except Exception as e:
                            expiry_date = None

                        __payment_detail__ = PaymentDetail()
                        __payment_detail__.customer_name = __auth__[
                            'account_name']
                        __payment_detail__.expiry_date = expiry_date
                        __payment_detail__.issuer = __auth__['bank']
                        __payment_detail__.card_brand = __auth__['card_type']
                        __payment_detail__.mandate_review = __mandate_review__
                        __payment_detail__.save()

            except Exception as e:
                """ save the reason why it failed """
                print(e)
        return __verification__
