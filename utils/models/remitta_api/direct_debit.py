"""
The Direct Debit API on Remita allows you to withdraw funds from your customers' account(s) via mandate(s) issued to you by the customer(s) through their bank(s). Using the methods exposed by this API, you will be able to credit your account(s) by debiting your customers' bank accounts for products sold and services rendered to a maximum of a certain amount for a specific number of times each calendar month.

Note
[-] Base URL for Sandbox Environment is http://www.remitademo.net
[-] Hashing is done using SHA512 algorithm
[-] See Appendix below for Description to Fields, Error Codes and Bank Codes
"""

import datetime
import json
import requests


from django.conf import settings


class DirectDebit:

    def __init__(self):
        self.end_point = settings.REMITTA
        self.mandate_setup = "{}{}".format(
            settings.REMITTA_PARAMS.URL, "mandate/setup")
        self.mandate_activation = "{}{}".format(
            settings.REMITTA_PARAMS.URL, "mandate/requestAuthorization")
        self.mandate_activation_validation = "{}{}".format(
            settings.REMITTA_PARAMS.URL, "mandate/validateAuthorization")
        self.cancel_debit_instructions_url = "{}{}".format(
            settings.REMITTA_PARAMS.URL, "mandate/payment/stop")
        self.issue_debit_instructions_url = "{}{}".format(
            settings.REMITTA_PARAMS.URL, "mandate/payment/send")

    def setup_reoccuring_payments(self, mandate, request_id, mandate_type, service_type):
        """
        Setup Recurring Payments
        API Name: SetUpMandate
        Request Method: POST
        Endpoint:/remita/exapp/api/v1/send/api/echannelsvc/echannel/mandate/setup

        service_type: product type

        SAMPLE RESPONSE:
        {
            "statuscode":"040",
            "mandateId":"290007625795",
            "status":"Initial Request OK"
        }
        """

        rentals = mandate.rentals.order_by('id')
        try:
            start_date = rentals.first().collection_date
            end_date = rentals.last().collection_date
        except:
            start_date = ''
            end_date = ''

        headers = {'content-type': 'application/json'}
        payload = {
            "merchantId":  settings.REMITTA_PARAMS.MERCHANT_ID, ,
            "serviceTypeId": service_type,
            "hash": settings.REMITTA_PARAMS.API_DETAILS_HASH,
            "payerName": mandate.customer.name(),
            "payerEmail": mandate.customer.email(),
            "payerPhone": mandate.customer.tel,
            "payerBankCode": mandate.customer.bank_detail.bank.abbreviation,
            "payerAccount": mandate.customer.bank_detail.account_number,
            "requestId":  request_id,
            "amount":  mandate.amount,
            "startDate": start_date,
            "endDate": end_date,
            "mandateType": mandate_type,
            "maxNoOfDebits":  mandate.rentals.count()
        }

        response = requests.post(
            self.mandate_setup, data=json.dumps(payload), headers=headers).json()
        return response

    def mandate_activation_request_otp(self, request_id, mandate):
        """
        Mandate Activation (Request OTP)
        API Name:MandateActivateRequestOtp
        Request Method:POST
        Endpoint: /remita/exapp/api/v1/send/api/echannelsvc/echannel/mandate/requestAuthorization

        HEADERS
        {
            Content-Type: application/json
            MERCHANT_ID: {{merchantId}}
            API_KEY: {{apiKey}}
            REQUEST_ID: {{requestId}}
            REQUEST_TS: {{timeStamp}}
            API_DETAILS_HASH: {{apiHash}}
        }

        SAMPLE RESPONSE
        {
            "statuscode": "00",
            "authParams": [
                {
                    "param1": "OTP",
                    "description1": "Please enter your Bank OTP"
                }
            ],
            "requestId": "1530526752288",
            "mandateId": "320007693658",
            "remitaTransRef": "1530529423084",
            "status": "SUCCESS"
        }
        """
        headers = {
            'content-type': 'application/json',
            "MERCHANT_ID": settings.REMITTA_PARAMS.MERCHANT_ID,
            "API_KEY": settings.REMITTA_PARAMS.API_KEY,
            "REQUEST_ID": request_id,
            "REQUEST_TS": datetime.datetime.now(),
            "API_DETAILS_HASH": settings.REMITTA_PARAMS.API_DETAILS_HASH,
        }
        payload = {
            "mandateId": mandate.code,
            "requestId": request_id
        }

        response = requests.post(self.mandate_activation, data=json.dumps(
            payload), headers=headers).json()
        return response

    def mandate_activation_validate_otp(self, reference_code, card, otp):
        """
        Mandate Activation (Validate OTP)
        API Name:MandateActivateValidateOtp
        Request Method:POST
        Endpoint:/remita/exapp/api/v1/send/api/echannelsvc/echannel/mandate/validateAuthorization

        HEADERS
        {
            Content-Type: application/json
            MERCHANT_ID: {{merchantId}}
            API_KEY: {{apiKey}}
            REQUEST_ID: {{requestId}}
            REQUEST_TS: {{timeStamp}}
            API_DETAILS_HASH: {{apiHash}}
        }

        SAMPLE RESPONSE 
        {
            "statuscode":"00",
            "mandateId":"320007693658",
            "status":"Mandate Activated Successfully"
        }
        """

        headers = {
            'content-type': 'application/json',
            "MERCHANT_ID": settings.REMITTA_PARAMS.MERCHANT_ID,
            "API_KEY": settings.REMITTA_PARAMS.API_KEY,
            "REQUEST_ID": request_id,
            "REQUEST_TS": datetime.datetime.now(),
            "API_DETAILS_HASH": settings.REMITTA_PARAMS.API_DETAILS_HASH,
        }
        payload = {
            "remitaTransRef": reference_code,
            "authParams": [
                {
                    "param1": "OTP",
                    "value": otp
                },
                {
                    "param2": "CARD",
                    "value": card
                }
            ]
        }

        response = requests.post(
            self.mandate_activation_validation, data=json.dumps(payload), headers=headers).json()
        return response

    def mandate_activation_notification(self, mandate_activation_notification_url=''):
        """
        Mandate Activation Notification
        We notify you of activated mandates in your favour 
        Request Method:POST 
        Endpoint:(Your Payment Notification URL)

        SAMPLE RESPONSE
        {
            "notificationType":"ACTIVATION",
            "lineItems":[
            {
                "mandateId":" 340007627867",
                "activationDate":"19/01/2015",
                "requestId":"23457885",
                "startDate":"12/02/2015",
                "endDate":"12/02/2016",
                "amount":"20000"
            },
            {
                "mandateId":" 347307627867",
                "activationDate":"19/01/2015",
                "requestId":"646743367",
                "startDate":"05/02/2015",
                "endDate":"12/02/2015",
                "amount":"50000"
            }
            ]
        }
        """
        response = request.post(mandate_activation_notification_url)
        return response

    def issue_debit_instructions(self):
        """
        Issue Debit Instructions
        API Name:SendDebitInstruction
        Request Method:POST
        Endpoint:/remita/exapp/api/v1/send/api/echannelsvc/echannel/mandate/payment/send

        SAMPLE RESPONSE
        {
            "mandateId":"320007693658",
            "rrr":"40007613498",
            "transactionRef":"290007625795",
            "statuscode":"01" "status":"Approved"
        }
        """

        payload = {
            "merchantId": " 27768931",
            "serviceTypeId": " 35126630",
            "hash": "duisaifnasfiouj329839Ufwnihj3",
            "requestId": "232345432",
            "totalAmount": "5000",
            "mandateId": " 320007693658",
            "fundingAccount": "1245125478",
            "fundingBankCode": "044"
        }
        response = request.post(
            self.issue_debit_instructions_url, data=json.dumps(payload))
        return response

    def debit_notification(self, debit_notification_url=''):
        """
        Debit Notification
        We notify you of debits collected in your favour

        Request Method:POST
        Endpoint:(Your Payment Notification URL)

        SAMPLE RESPONSE
        {
            "notificationType":"DEBIT",
            "lineItems":[
            {
                "mandateId":"320007693658",
                "debitDate":"03/05/2017",
                "requestId":"09432223433",
                "amount":"20000"
            }
            ]
        }
        """

        response = request.post(debit_notification_url).json()
        return response

    def cancel_debit_instructions(self):
        """
        Cancel Debit Instructions
        We notify you of debits collected in your favour
        API Name:CancelDebitInstruction
        Request Method:POST
        Endpoint:/remita/exapp/api/v1/send/api/echannelsvc/echannel/mandate/payment/stop

        HEADERS


        SAMPLE RESPONSE
        {
            "statuscode":"00",
            "mandateId":"290007625795",
            "status":"Completed Succesfully"
        }
        """

        payload = {
            "merchantId": " 27768931",
            "mandateId": " 320007693658",
            "hash": "7689uy2h83ynejw92892",
            "transactionRef": "114577269383",
            "requestId": "637283767"
        }
        response = request.post(
            self.cancel_debit_instructions_url, data=json.dumps(payload))
        return response


    
