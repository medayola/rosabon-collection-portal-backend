from django.test import TestCase
from payment.transaction import PaystackTransaction
from django.conf import settings


class TestPyStack(TestCase):
    pystack = None

    def setUp(self):
        self.pystack = PaystackTransaction(
            authorization_key=settings.PAYSTACK_AUTHORIZATION_KEY)

    def test_can_charge_bulk(self):
        payload = [
            dict(authorization="AUTH_akm42n5tjx",
                 amount="999999999999999999", attempt_partial_debit=False),
            dict(authorization="AUTH_137cx2qchn",
                 amount="23000000", attempt_partial_debit=True),
        ]
        status, success, message, response = self.pystack.charge_bulk(
            payload=payload)

        self.assertEqual({
            "status": True,
            "message": message,
            "data": {
                "domain": "test",
                "status": "active",
                "total_charges": 2,
                "pending_charges": 2
            }
        }, {
            "status": True,
            "message": message,
            "data": {
                "domain": response['domain'],
                "status": response['status'],
                "total_charges": 2,
                "pending_charges": 2
            }
        })

    # def test_can_fetch_bulk(self):
    #     id = "1487819"
    #     response = self.pystack.fetch_bulk_charge_response(charge_id=id)
    #     status, success, message, response = response
    #     self.assertEqual({
    #         "status": True,
    #         "message": message,
    #         "data": {
    #             "domain": "test",
    #             "status": "active",
    #             "total_charges": 2,
    #             "pending_charges": 2
    #         }
    #     }, {
    #         "status": True,
    #         "message": message,
    #         "data": {
    #             "domain": response['domain'],
    #             "status": response['status'],
    #             "total_charges": 2,
    #             "pending_charges": 2
    #         }
    #     })

    