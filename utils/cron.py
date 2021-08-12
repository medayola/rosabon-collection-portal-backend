import datetime

from django.conf import settings
from django.db import transaction
from django.db.models import Q

from payment.transaction import PaystackTransaction
from pipeline.models import PaystackQueue

from pypaystack import version
import numpy as np
import pandas as pd
import requests

from mandates.models import Rental
from mandates.models import Mandate
from mandates.models import Trial

from utils.report_generator import ReportGenerator
from django.core.mail import EmailMessage


class FetchPaystackPayments:
    """
    A class to periodically fetch paystack payments
    """

    _CONTENT_TYPE = "application/json"
    _BASE_END_POINT = "https://api.paystack.co"

    def __init__(self):
        self.queryset = Rental.objects
        self.pystack = PaystackTransaction(
            authorization_key=settings.PAYSTACK_AUTHORIZATION_KEY)

    def disable_old_rentals(self):
        today = datetime.date.today()
        before = today - datetime.timedelta(days=-90)

        queryset = self.queryset.filter(
            collection_status=Rental.ACTIVE,
            mandate__payment_option=Mandate.PAYSTACK
        ).exclude(collection_date__gte=before).distinct()

        with transaction.atomic():
            for i in queryset.order_by('id'):
                i.collection_status = Rental.FAILED
                i.save()

    def debit_runner(self, rentals, head=0):
        head += 1
        if head <= 5:
            def changer(t): return t.get('amount')/head
            changed_rentals = [rent for rent in [
                changer(rental) for rental in rentals] if rent.amount > 1000]
            _ = self.pystack.charge_bulk(changed_rentals)

    def fetch_payments(self):
        # fetch active mandates
        mandates = Mandate.objects.filter(
            payment_option=Mandate.PAYSTACK,
            rentals__collection_status=Rental.ACTIVE,
            status=Mandate.ACTIVE
        ).distinct()
        print('got {} mandates'.format(mandates.count()))

        # fetch all active rentals
        queryset = [
            i.rentals.filter(
                collection_status=Rental.ACTIVE
            ).order_by(
                'collection_date'
            ).last() for i in mandates]

        print('qs: {}', len(queryset))

        queryset = Rental.objects.filter(
            id__in=[
                i.id for i in queryset
            ]
        ).distinct()

        rentals = []
        for qs in queryset:
            try:
                if qs.pending_amount is None:
                    print(qs, 'is None(0)\n\n')
                if (qs.pending_amount * 100) > settings.PAYSTACK_MAX_AMOUNT:
                    pending_amount = round(
                        settings.PAYSTACK_MAX_AMOUNT / 100.00, 2)
                else:
                    pending_amount = round(qs.pending_amount, 2)

                if pending_amount is None:
                    print(qs, 'is None\n\n')

                balance = int(pending_amount * 100)
                at_least = int(balance / 10)
                if balance > 0 and balance < settings.PAYSTACK_MIN_AMOUNT:
                    at_least = balance
                else:
                    at_least = settings.PAYSTACK_MIN_AMOUNT

                result = {
                    "authorization": qs.mandate.authorization_code,
                    "amount": int(pending_amount * 100),
                    "attempt_partial_debit":
                    balance > settings.PAYSTACK_MIN_AMOUNT,
                    "at_least": at_least,
                    "metadata": {
                        "custom_fields": [
                            {
                                "display_name": "Rental Id",
                                "variable_name": "rental_id",
                                "value": qs.id
                            }
                        ]
                    }
                }

                if pending_amount > 0:
                    rentals.append(result)
            except Exception as e:
                print(e)

        print('rentals: ', rentals, qs)
        try:
            df = pd.DataFrame(rentals)
            df.to_excel("rentals-{}.xlsx".format(
                str(datetime.datetime.now().timestamp()).replace('.', '')))
            """ print rentals to file """
        except Exception as exception:
            print(exception)

        (
            response_status_code,
            response_status,
            response_message,
            response_data
        ) = self.pystack.charge_bulk(rentals)
        """ bulk fetch the rentals """

        print('pp: ', response_message, response_status, response_status_code)
        if response_status_code == 200 and response_status:
            queue = PaystackQueue.objects.filter(
                status=True,
                batch_id=response_data['id']
            ).order_by('created_at').first()
            if queue is None:
                queue = PaystackQueue.objects.create(
                    status=True,
                    batch_id=response_data['id']
                )
            return True
        return False

    def activate_rentals(self):
        queryset = self.queryset.filter(
            collection_status=Rental.PENDING,
            mandate__status=Mandate.ACTIVE,
            mandate__payment_option=Mandate.PAYSTACK,
            collection_date__lte=datetime.date.today()
        ).distinct()

        with transaction.atomic():
            # activate them all
            for active in queryset:
                active.collection_status = Rental.ACTIVE
                active.save()

    def update_trials(self, data):
        still_active = False
        for item in data:
            if item.get('transaction', None):
                transaction = item.get('transaction')
                if transaction.get('metadata', None):
                    metadata = transaction.get('metadata')
                    rental_attr = metadata.get('custom_fields')[0]

                    if rental_attr.get('variable_name') == "rental_id":
                        try:
                            rental = Rental.objects.get(
                                pk=rental_attr.get('value'))
                            msg = item.get('message')
                            amount = item.get('amount') / 100.00
                            ref = transaction.get('id')

                            Trial.objects.get_or_create(
                                reference_code=ref,
                                rental=rental,
                                collected_amount=amount,
                                defaults={
                                    'status': item.get('status') == "success",
                                    'message': msg
                                }
                            )
                        except Exception as e:
                            print(e)
                            still_active = True

        return still_active

    def confirm_payments(self):
        still_active = False

        # get the last active batch id
        last_active_batch = PaystackQueue.objects.filter(
            status=True
        ).order_by(
            'batch_id'
        ).last()

        items = np.array([])

        print('last_active_batch: ', last_active_batch)

        with transaction.atomic():
            # query the server for the data
            if last_active_batch is not None:

                status, message, data, meta = self.expand_response(
                    last_active_batch.batch_id)

                if status:
                    page_count = int(meta.get('pageCount', 0))
                    try:
                        items = np.concatenate((items, data), axis=0)
                    except Exception:
                        still_active = True
                    for page in range(2, page_count + 1):
                        try:
                            status_, msg, data, met = self.expand_response(
                                last_active_batch.batch_id, page)
                        except Exception as e:
                            print(e)
                            still_active = True
                        if status_:
                            items = np.concatenate((items, data), axis=0)

                    still_active = self.update_trials(items)
                else:
                    still_active = True
                last_active_batch.status = still_active
                last_active_batch.save()

        return still_active

    def parse_charges(self, batch_id, page):
        url = "{}/bulkcharge/{}/charges?page={}".format(
            self._BASE_END_POINT,
            batch_id,
            page
        )
        headers = {
            "Content-Type": self._CONTENT_TYPE,
            "Authorization": "Bearer " + settings.PAYSTACK_AUTHORIZATION_KEY,
            "user-agent": "pyPaystack-{}".format(version.__version__)
        }

        return requests.get(url=url, headers=headers)

    def expand_response(self, batch_id, page=1):

        try:
            response = self.parse_charges(batch_id=batch_id, page=page)
            if response.status_code == 404:
                return False

            if response.status_code in [200, 201]:
                parsed_response = response.json()

                status = parsed_response.get('status', None)
                message = parsed_response.get('message', None)
                data = parsed_response.get('data', None)
                meta = parsed_response.get('meta', None)

                return status, message, data, meta
        except Exception:
            return False, None, [], None

    def mature_mandates(self):
        """
            method to fetch all mandates that:
            - are active.
            - have all their rentals as:
                - success
                - manual_success
            - last due date has passed
        """

        mandates = Mandate.objects
        mandates = mandates.filter(status=Mandate.ACTIVE)
        mandates = mandates.filter(
            Q(rentals__collection_status=Rental.SUCCESS) |
            Q(rentals__collection_status=Rental.MANUAL_SUCCESS)
        )
        mandates = [
            m for m in mandates
            if m.has_expired()
        ]

        print(mandates)


class WeeklyReport:
    """ class to generate weekly reports """

    def __init__(self):
        self.end_date = datetime.date.today()
        self.generator = ReportGenerator()

    def get_start_date(self):
        return self.end_date + datetime.timedelta(-7)

    def generate_doc(self, print_text=False):
        self.generator.end_date = self.end_date
        self.generator.start_date = self.get_start_date()

        self.generator.resolve_weekly_report()
        self.generator.printer.print()


class MonthlyReport:
    """ class to generate monthly reports """

    def __init__(self):
        self.end_date = datetime.date.today()
        self.generator = ReportGenerator()

    def get_start_date(self):
        return self.end_date + datetime.timedelta(-7)

    def generate_doc(self, print_text=False):
        self.generator.end_date = self.end_date
        self.generator.start_date = self.get_start_date()

        self.generator.resolve_weekly_report()
        self.generator.printer.print()


def fetch_paystack_payments():
    try:
        param = FetchPaystackPayments()
        param.activate_rentals()
        item = param.fetch_payments()
        print(f'Fetching pp data {item}')
        return True
    except Exception as e:
        print(e)
        return False


def confirm_trials_status():
    try:
        param = FetchPaystackPayments()
        param.activate_rentals()
        param.confirm_payments()
        return True
    except Exception:
        return False


def fail_paystack_payments():
    try:
        param = FetchPaystackPayments()
        param.disable_old_rentals()
        return True
    except Exception:
        return False


def activate_paystack_rentals():
    try:
        param = FetchPaystackPayments()
        param.activate_rentals()
        return True
    except Exception:
        return False


def send_weekly_report():
    """
        Weekly reports are sent generated and sent every thursday
    """
    weekly_report = WeeklyReport()
    weekly_report.generate_doc()

    # send email to
    to = [

        't.odubayo@rosabon-finance.com',
        'i.patrick@rosabon-finance.com',
        'ebele.okoli@rosabon-finance.com',
        'chinedu.elesi@rosabon-finance.com',
        'omowumi.olaleye@rosabon-finance.com',
        'boniface.musa@rosabon-finance.com',
        'esther.adeyinka@rosabon-finance.com',
        'ijeoma.olisa@rosabon-finance.com',
        'collections@rosabon-finance.com',
        'fatimah.alayaki@concept-nova.com',

    ]

    subject = weekly_report.generator.printer.filename.split('.')[0]
    message = EmailMessage(
        subject=subject,
        body='Kindly find attached ' + subject,
        from_email='"{}"<{}>'.format(
            settings.DEFAULT_FROM_NAME,
            settings.DEFAULT_FROM_EMAIL
        ),
        to=to
    )
    message.attach_file(weekly_report.generator.printer.file_url)
    message.send(fail_silently=True)
