from django.shortcuts import redirect
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

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
