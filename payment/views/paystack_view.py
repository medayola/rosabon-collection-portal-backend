from django.shortcuts import redirect
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import hmac
import urllib.parse
import hashlib
from mandates.models import Trial, Rental
from payment.serializers.paystack_serializer import PaystackSerializer


class PaystackPayment(APIView):
    """
    Route to authenticate payment for paystack
    """

    def get(self, request, *args, **kwargs):
        serializer = PaystackSerializer(data=request.GET)
        if serializer.is_valid():
            serializer.validate_reference_code(
                reference=serializer.data['reference'])
            return redirect(settings.PAYSTACK_CALLBACK_PAGE)
            # return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaystackWebhook(APIView):

    def post(self, request, *args, **kwargs):
        try:
            print(request.data)
            # check if content exists
            data = request.data
            if data is None:
                raise Exception("No data")

            # check hash headers
            paystack_hash = request.headers.get('x-paystack-signature', None)
            if paystack_hash is None:
                raise Exception("x-paystack-signature required")

            # verify paystack signature
            paybytes = urllib.parse.urlencode(data).encode('utf8')
            new_hash = hmac.new(settings.PAYSTACK_AUTHORIZATION_KEY, paybytes, hashlib.sha512).hexdigest()
            if paystack_hash != new_hash:
                raise Exception("Invalid signature.")

            # get event data
            event = data.get('event', None)
            if event is None:
                raise Exception("No event property found")

            if event == "charge.success":
                if data.get('data', None):
                    transaction = data.get('data', None)
                    if transaction and transaction.get('metadata', None):
                        metadata = transaction.get('metadata')
                        rental_attr = metadata.get('custom_fields')[0]
                        if rental_attr.get('variable_name') == "rental_id":
                            rental = Rental.objects.get(
                                pk=rental_attr.get('value'))
                            msg = transaction.get('message')
                            amount = transaction.get('amount') / 100.00
                            ref = transaction.get('id')

                            Trial.objects.get_or_create(
                                reference_code=ref,
                                rental=rental,
                                collected_amount=amount,
                                defaults={
                                    'status': transaction.get('status') == "success",
                                    'message': msg
                                }
                            )
                            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
