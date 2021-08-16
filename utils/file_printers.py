from datetime import datetime

import pandas as pd
from django.conf import settings
from django.db.models import Q
from dateutil.relativedelta import relativedelta

from pipeline.models import MandateReview
from mandates.models import Rental, Trial, Mandate


class PDFPrinter:
    @staticmethod
    def print_to_file(mandates, name='output'):
        return 'hi'


class ExcelPrinter:

    # @staticmethod
    # def __

    @staticmethod
    def __format_mandates__(mandates):
        response = []
        for key, mandate in enumerate(mandates):
            bank = mandate.customer.bank_detail
            if bank is not None:
                bank_name = bank.bank.name
                bank_account = bank.account_number
            else:
                bank_name = '--'
                bank_account = '--'

            __next_date__ = mandate.rentals.filter(
                collection_status=Rental.ACTIVE
            ).order_by('-id').first()
            if __next_date__ is None:
                __next_date__ = '--'
            else:
                try:
                    __next_date__ = __next_date__.collection_date.strftime(
                        '%m/%d/%Y')
                except Exception:
                    __next_date__ = '--'

            __last_date__ = mandate.rentals.order_by('-id').first()
            if __last_date__ is None:
                __last_date__ = '--'
            else:
                try:
                    __last_date__ = __last_date__.collection_date.strftime(
                        '%m/%d/%Y')
                except Exception:
                    __last_date__ = '--'

            try:
                __first_trial__ = mandate.trials().first().created_at.strftime(
                    '%m/%d/%Y')
            except Exception:
                __first_trial__ = '--'

            try:
                __last_trial__ = mandate.trials().last().created_at.strftime(
                    '%m/%d/%Y')
            except Exception:
                __last_trial__ = '--'

            try:
                __activated_date__ = mandate.activated_date.strftime(
                    '%m/%d/%Y')
            except Exception:
                __activated_date__ = '--'

            response.append([
                (key + 1),
                mandate.customer.name(),
                mandate.status,
                bank_name,
                bank_account,
                mandate.amount,
                mandate.created_at.strftime('%m/%d/%Y'),
                __activated_date__,
                mandate.initial_repayment_date.strftime('%m/%d/%Y'),
                __first_trial__,
                __last_trial__,
                mandate.rentals.filter(
                    collection_status=Rental.SUCCESS
                ).count(),
                __next_date__,
                __last_date__
            ])
        return response

    @staticmethod
    def print_to_file(mandates, name='output'):
        columns = [
            'S/N',
            'PAYER NAME',
            'STATUS',
            'PAYER BANK',
            'PAYER ACCOUNT',
            'AMOUNT',
            'REG. DATE',
            'ACTIVATED DATE',
            'START DATE',
            'LAST TRXN. DATE',
            'LAST TRXN. STATUS',
            'SUCCESSFUL PAYMENTS',
            'LAST DUE DATE',
            'END DATE', ]

        response = ExcelPrinter.__format_mandates__(mandates)
        index = [i for i in range(1, len(response) + 1)]
        dataframe = pd.DataFrame(
            response,
            index=index,
            columns=columns
        )

        # create the excel sheet
        __root_name__ = '{}.xlsx'.format(name)
        __base__ = '{}'.format('_'.join(__root_name__.split(' ')))
        __url__ = '{}{}'.format(settings.MEDIA_URL, __base__)

        __name__ = '{}{}'.format(settings.MEDIA_ROOT, __base__)

        dataframe.to_excel(__name__)
        return __root_name__, __url__


class PandasPrinter:

    def __init__(self, data=[], filename="output"):
        """
        Constructor for the Pandas Printer class

        Parameters:
            data - the data to display
            filename - the filename to create
        """

        self.data = data

        self.sheet_data = {}
        """ formatted data """

        self.filename = filename
        self.filetype = settings.EXCEL
        self.headers = []

        self.media_url = ""
        self.file_url = ""

    def get_lastpayment_date(self, mandate):

        last_payment_date = mandate.rentals.filter(
            Q(collection_status=Rental.SUCCESS) |
            Q(collection_status=Rental.MANUAL_SUCCESS)

        ).order_by(
            '-collection_date'
        )

        if last_payment_date.exists():
            last_payment_date = last_payment_date.first().collection_date.strftime(
                '%d/%b/%Y'
            )

        else:
            last_payment_date = "N/A"

        return last_payment_date

    def generate_mandates_report(self):
        print("The values of the sheet", self.sheet_data)
        """
        Generates an excel sheet to display all the mandates
        within a time range
        """

        self.sheet_data = []

        for k, v in enumerate(self.data):

            last_message = ''
            last_status = ''
            last_date = ''
            next_due_date = ''
            end_date = ''

            trial = Trial.objects.filter(
                rental__mandate=v
            ).order_by('created_at').last()

            next_rental = v.rentals.filter(
                collection_status=Rental.PENDING
            ).order_by(
                'collection_date'
            ).first()

            last_rental = v.rentals.order_by(
                'collection_date'
            ).last()

            mandate_review = MandateReview.objects.filter(mandate=v.id).first()

            if trial is not None:
                last_message = trial.message
                last_status = trial.status
                last_date = trial.created_at.strftime('%d/%b/%Y')

            if next_rental is not None:
                next_due_date = next_rental.collection_date.strftime(
                    '%d/%b/%Y')

            if last_rental is not None:
                next_due_date = last_rental.collection_date.strftime('%d/%b/%Y')

            activated_date = ''
            if v.activated_date is not None:
                activated_date = v.activated_date.strftime('%d/%b/%Y')

            initial_repayment_date = ''
            if v.initial_repayment_date is not None:
                due_date = v.initial_repayment_date
                initial_repayment_date = due_date
                end_date = due_date + relativedelta(months=int(v.tenure))
                end_date = end_date
                next_du_date = initial_repayment_date + relativedelta(months=1)
                next_du_date = next_du_date

            created_at = ''
            if v.created_at is not None:
                created_at = v.created_at.strftime('%d/%b/%Y')

            self.sheet_data.append({
                "Authorization Code": v.authorization_code,
                "Bank": v.customer.bank_detail.bank,
                "Branch": v.customer.branch,
                "Customer Name": v.customer.fullname(),
                "Phone Number": v.customer.tel,
                "Payer Email": v.customer.email(),
                "Product": v.product.name,
                "Rental Amount": round(v.amount, 2),
                "Start Date": initial_repayment_date.strftime('%d/%b/%Y'),
                "End Date": end_date.strftime('%d/%b/%Y'),
                "Next Due Date": next_du_date.strftime('%d/%b/%Y'),
                "Tenor": v.tenure,
                "Mandate Status": v.status,
                "Payer Account": v.customer.bank_detail.account_number,
                "Registration Date": created_at,
                "Activated Date": activated_date,
                "Last Trxn Date": last_date,
                "Last Trxn Message": last_message,
                "Last Trxn Status": last_status,
                "No of Pending Rentals Status": v.rentals.filter(
                    Q(collection_date__lte=end_date, collection_status=Rental.PENDING)).count(),
                "No of Outstanding Rentals Status": v.rentals.filter(Q(collection_status=Rental.PENDING)).count(),
                "Total Amount Collected": v.total_collected(),
                "Initial Comment": mandate_review.get_initial_comment if mandate_review else None,
                "Approval Comment": mandate_review.get_approval_comment if mandate_review else None,
                "Account officer name": v.account_officer.name(),
                "Account officer email": v.account_officer.email(),
                "Successful Payments": v.rentals.filter(
                    Q(collection_status=Rental.SUCCESS) |
                    Q(collection_status=Rental.MANUAL_SUCCESS)).count(),
                "Last Due Date": next_due_date,

            })

    def generate_transactions_report(self):
        """
        Generates an excel sheet to display all the transactions
        on the portal within a time range
        """

        self.headers = [
            "s/n",
            "payer name",
            "payer email address",
            "payer bank",
            "trxn date",
            "trxn ref",
            "payment status", ]
        """ the headers for the excel sheet """

    def generate_excd_recvd_for_the_wk(self):
        """
        Generates an excel sheet to display all the expected and recieved
        payments for the week
        """

        self.headers = [
            "s/n",
            "mandate auth code",
            "payer name",
            "payer email address",
            "payer bank",
            "branch",
            "Product Type",
            "Start Date",
            "End Date",
            "Due Date",
            "Expected amount",
            "Received amount",
            "Outstanding Rentals",
            "mandate status",
            "Last Payment Date"
        ]
        """ the headers for the excel sheet """

    def generate_recvd_for_the_range(self, end_date):

        print("This is a test")
        """
        Generates an excel sheet to display all the recieved
        payments within a range of dates
        """
        self.sheet_data = {}
        sheet_data = [
            dict(
                id=value.rental.mandate.id,
                code=value.rental.mandate.authorization_code,
                name=value.rental.mandate.customer.fullname(),
                email=value.rental.mandate.customer.email(),
                bank=value.rental.mandate.customer.bank_detail.bank.name,
                branch=value.rental.mandate.customer.branch,
                collected_amount=value.collected_amount,
                product=value.rental.mandate.product.name,
                start_date=value.rental.mandate.get_start_date.strftime('%d/%b/%Y'),
                end_date=value.rental.mandate.get_end_date.strftime('%d/%b/%Y'),
                due_date=value.rental.mandate.get_due_date.strftime('%d/%b/%Y'),
                last_trxn_date=value.created_at.strftime('%d/%b/%Y'),
                last_trxn_status=value.status,
                paid_rentals=value.rental.mandate.rentals.filter(
                    Q(collection_status=Rental.SUCCESS) |
                    Q(collection_status=Rental.MANUAL_SUCCESS)).count(),
                outstanding_rentals=value.rental.mandate.rentals.filter(Q(collection_status=Rental.PENDING)).count(),
                pending_rentals=value.rental.mandate.rentals.filter(
                    Q(collection_date__lte=end_date, collection_status=Rental.PENDING, )).count(),
                mandate_status=value.rental.mandate.status,
                last_payment_date=self.get_lastpayment_date(value.rental.mandate),
            )
            for key, value in enumerate(self.data)
        ]
        i = 0
        for value in sheet_data:
            key = f"{value.get('id')}"
            i += 1
            if key not in self.sheet_data:
                self.sheet_data[key] = {
                    "S/N": i,
                    "Authorization Code": value.get('code'),
                    "Payer Name": str(value.get('name')).title(),
                    "Payer Email": str(value.get('email')).lower(),
                    "Payer Bank": value.get('bank'),
                    "Branch": value.get('branch'),
                    "Collected Amount": round(value.get('collected_amount'), 2),
                    "Last TRXN Date": value.get('last_trxn_date'),
                    "Last TRXN Status": value.get('last_trxn_status'),
                    "Start Date": value.get("start_date"),
                    "End Date": value.get('end_date'),
                    "Due Date": value.get('due_date'),
                    "No of Outstanding Rentals": value.get("outstanding_rentals"),
                    "No of Pending Rentals": value.get("pending_rentals"),
                    "Product Type": value.get('product'),
                    "Mandate Status": value.get('mandate_status'),
                    "Last Payment Date":value.get('last_payment_date'),

                }
            else:
                collected_amount = self.sheet_data[key].get(
                    'Collected Amount') + value.get('collected_amount')

                self.sheet_data[key].update({
                    "Collected Amount": round(collected_amount, 2)})

        self.sheet_data = [v for _, v in self.sheet_data.items()]
        # return [v for _, v in self.sheet_data.items()]
        print("this is the sheet data", self.sheet_data)

    def generate_excd_for_the_range(self, end_date):
        """
        Generates an excel sheet to display all the expected
        payments within a range of dates
        """
        self.sheet_data = {}
        sheet_data = [
            dict(
                id=value.mandate.id,
                code=value.mandate.authorization_code,
                name=str(value.mandate.customer.fullname()).title(),
                email=value.mandate.customer.email(),
                branch=value.mandate.customer.branch,
                bank=value.mandate.customer.bank_detail.bank.name,
                expected_amount=value.mandate.amount,
                expected_date=value.collection_date,
                start_date=value.mandate.get_start_date.strftime('%d/%b/%Y'),
                end_date=value.mandate.get_end_date.strftime('%d/%b/%Y'),
                due_date=value.mandate.get_due_date.strftime('%d/%b/%Y'),
                paid_rentals=value.mandate.rentals.filter(
                    Q(collection_status=Rental.SUCCESS) |
                    Q(collection_status=Rental.MANUAL_SUCCESS)).count(),
                pending_rentals=value.mandate.rentals.filter(
                    Q(collection_date__lte=end_date, collection_status=Rental.PENDING)).count(),
                outstanding_rentals=value.mandate.rentals.filter(Q(collection_status=Rental.PENDING)).count(),
                product=value.mandate.product.name,
                mandate_status=value.mandate.status,
                last_payment_date=self.get_lastpayment_date(value.mandate),
            )
            for key, value in enumerate(self.data)
        ]
        i = 0
        for value in sheet_data:
            key = f"{value.get('id')}"
            i += 1
            if key not in self.sheet_data:
                self.sheet_data[(key)] = {
                    "S/N": i,
                    "Authorization Code": value.get('code'),
                    "Payer Name": value.get('name'),
                    "Payer Email": value.get('email'),
                    "Payer Bank": value.get('bank'),
                    "Branch": value.get('branch'),
                    "Expected Amount": round(value.get('expected_amount'), 2),
                    "Start Date": value.get('start_date'),
                    "End Date": value.get('end_date'),
                    "Due Date": value.get('due_date'),
                    "Paid Rentals": round(value.get('paid_rentals'), 2),
                    "Pending Rentals": round(value.get('pending_rentals'), 2),
                    "Outstanding Rentals": round(value.get('outstanding_rentals'), 2),
                    "Product Type": value.get('product'),
                    "Mandate Status": value.get('mandate_status'),
                    "Last Payment Date": value.get('last_payment_date'),
                }

            else:

                expected_amount = self.sheet_data[key].get(
                    "Expected Amount") + value.get('expected_amount')

                self.sheet_data[key].update({
                    "Expected Amount": round(expected_amount, 2)})
        print("sheet data{}".format(self.sheet_data))
        self.sheet_data = [v for _, v in self.sheet_data.items()]

    def generate_weekly_report(self, start_date, end_date):
        """
        Generates an excel sheet to display the weekly report
        for collections unit of CRM
        """
        print("I want to be sure this is the method")

        data = []
        try:
            for k, mandate in enumerate(self.data):

                initial_repayment_date = mandate.initial_repayment_date
                # due_date = initial_repayment_date + relativedelta(months=1)


                initial_repayment_date = initial_repayment_date.strftime(
                    '%d/%b/%Y')

                last_repayment_date = mandate.rentals.order_by(
                    '-collection_date'
                ).first().collection_date.strftime(
                    '%d/%b/%Y'
                )

                last_payment_date = mandate.rentals.filter(
                    Q(collection_status=Rental.SUCCESS) |
                    Q(collection_status=Rental.MANUAL_SUCCESS)

                ).order_by(
                    '-collection_date'
                )

                if last_payment_date.exists():
                    last_payment_date = last_payment_date.first().collection_date.strftime(
                        '%d/%b/%Y'
                    )

                else:
                    last_payment_date = " "

                expected = mandate.rentals.filter(
                    collection_date__lte=end_date
                ).count()

                successfull = mandate.rentals.filter(
                    Q(collection_date__lte=end_date),
                    Q(collection_status=Rental.SUCCESS) |
                    Q(collection_status=Rental.MANUAL_SUCCESS)
                ).count()

                outstanding = mandate.rentals.filter(
                    Q(collection_status=Rental.PENDING)
                ).count()

                mandate_review = MandateReview.objects.filter(mandate=mandate.id).first()

                pending = mandate.rentals.filter(
                    collection_date__lte=end_date,
                    collection_status=Rental.ACTIVE
                ).count()

                has_partial = mandate.rentals.filter(
                    collection_date__lte=end_date,
                    collection_status=Rental.ACTIVE
                ).order_by(
                    '-collection_date'
                ).first()

                if has_partial:
                    partial = has_partial.pending_amount < mandate.amount
                else:
                    partial = False

                no_of_defaults = mandate.rentals.filter(
                    collection_status=Rental.FAILED
                ).count()

                trials = Trial.objects.filter(
                    rental__mandate=mandate,
                    created_at__range=(
                        start_date, end_date
                    )
                ).order_by('-id')

                if len(trials) > 0:
                    amount_collected = sum(
                        [
                            i.collected_amount
                            for i in trials.filter(status=True)
                        ]
                    )

                    last_trxn_date = trials.last().updated_at
                    last_trxn_status = trials.last().status


                else:
                    amount_collected = 0.00
                    last_trxn_date = None
                    last_trxn_status = ""

                dictionary = {
                    "Authorization Code": mandate.authorization_code,
                    "Bank": mandate.customer.bank_detail.bank,
                    "Branch": mandate.customer.branch,
                    "Customer Name": mandate.customer.fullname(),
                    "Phone Number": mandate.customer.tel,
                    "Customer Email": mandate.customer.email(),
                    "Product": mandate.product,
                    "Rental Amount": round(mandate.amount, 2),
                    "Start Date": initial_repayment_date,
                    "Final End Date": last_repayment_date,
                    "Due Date": mandate.get_due_date.strftime('%d/%b/%Y'),
                    "Tenor": mandate.tenure,
                    "Expected Rental to date": expected,
                    "Successful via Paystack & Transfer": successfull,
                    "No of pending Rentals": pending,
                    "No of Outstanding Rentals": outstanding,
                    "Partial Payment": partial,
                    "Amount Collected": amount_collected,
                    "No. of Defaults": no_of_defaults,
                    "Last TRXN Date": last_trxn_date,
                    "Last TRXN Status": last_trxn_status,
                    "Last Payment Date": last_payment_date,
                    "Mandate Deactivated Date": mandate.deactivated_date,
                    "Initiated comment": mandate_review.get_initial_comment if mandate_review else None,
                    "Approved comment": mandate_review.get_approval_comment if mandate_review else None,
                    "Account officer name": mandate.account_officer.name(),
                    "Account officer email": mandate.account_officer.email(),
                    "Mandate status": mandate.status,
                }

                data.append(dictionary)
            self.sheet_data = data
            print("this is the data", data)
            return True
        except Exception as e:
            print(e)
            return False

    def print(self):
        """ create the report sheet """

        __base__ = '{}'.format('_'.join(self.filename.split(' ')))

        self.media_url = f"{settings.MEDIA_URL}{__base__}"
        self.file_url = f"{settings.MEDIA_ROOT}{__base__}"

        if self.filetype == settings.PDF:
            self.file_url = f"{self.file_url}.pdf"
            self.filename = f"{self.filename}.pdf"
            self.media_url = f"{self.media_url}.pdf"

        else:
            self.file_url = f"{self.file_url}.xlsx"
            self.filename = f"{self.filename}.xlsx"
            self.media_url = f"{self.media_url}.xlsx"
            pd.DataFrame(self.sheet_data).to_excel(self.file_url, index=False)
