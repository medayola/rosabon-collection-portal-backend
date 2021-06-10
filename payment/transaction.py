from pypaystack import utils, Transaction
import requests


class PaystackTransaction(Transaction):

    def initialize(self, email, amount, plan=None, reference=None, channel=None, metadata=None, callback_url=None):
        """
        Initialize a transaction and returns the response

        args:
        email -- Customer's email address
        amount -- Amount to charge
        plan -- optional
        Reference -- optional
        channel -- channel type to use
        metadata -- a list if json data objects/dicts
        callback_url -- a callback url for the request
        """
        amount = utils.validate_amount(amount)

        if not email:
            raise InvalidDataError(
                "Customer's Email is required for initialization")

        url = self._url("/transaction/initialize")
        payload = {
            "email": email,
            "amount": amount,
            "reference": reference,
            "plan": plan,
            "channels": channel,
            "metadata": {"custom_fields": metadata}
        }

        # if a callback url is sent add to request
        if callback_url is not None:
            payload['callback_url'] = callback_url

        return self._handle_request('POST', url, payload)

    def check(self, authorization_code=None, amount=0, email=None, currency='NGN'):
        """
        All mastercard and visa authorizations can be checked with 
        this endpoint to know if they have funds for the payment you seek
        """

        if not email:
            raise Exception("Customer's Email is required to charge")

        if not authorization_code:
            raise Exception(
                "Customer's Authorization Code is required to charge")

        amount = utils.validate_amount(amount)
        url = self._url("/transaction/check_authorization")
        payload = {
            "authorization_code": authorization_code,
            "amount": amount,
            "email": email,
            "currency": currency
        }
        return self._handle_request('POST', url, payload)

    def fetch_customer(
            self, email=None, currency='NGN', authorization_code=None):
        """
        All mastercard and visa authorizations can be checked with 
        this endpoint to know if they have funds for the payment you seek
        """

        if not email:
            raise Exception("Customer's Email is required to charge")

        if not authorization_code:
            raise Exception(
                "Customer's Authorization Code is required to charge")

        amount = utils.validate_amount(0.0)
        url = self._url("/transaction/check_authorization")
        payload = {
            "authorization_code": authorization_code,
            "amount": amount,
            "email": email,
            "currency": currency
        }
        return self._handle_request('POST', url, payload)

    def charge_bulk(self, payload):
        uri = 'https://api.paystack.co/bulkcharge'
        response = self._handle_request('POST', uri, payload)
        return response

    def extract_rental(self, obj):
        # authorization = obj.get('authorization').get('authorization_code')
        # return
        pass

    def fetch_bulk_charge_response(self, charge_id, page_number=1):
        uri = 'https://api.paystack.co/bulkcharge'
        uri = f'{uri}/{charge_id}/charges?page={page_number}'
        response = self._handle_request('GET', uri)
        return response
