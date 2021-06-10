import calendar
import datetime
import random

from django.db import transaction
from django.test import TestCase
from faker import Faker

from common.tests.test_graphql import CommonAppTest
from customers.models import Customer
from customers.tests.test_graphql import CustomerAppTest
from mandates.models import Mandate, Rental
from pipeline.models import MandateReview
from pipeline.models import PaystackQueue
from pipeline.tests.test_graphql import PipelineAppTest
from staff.tests.test_graphql import StaffAppTest
from utils import cron


class TestUtilsMethods(TestCase):
    def setUp(self):
        self.staff = StaffAppTest.create_staff()
        self.faker = Faker()

    @staticmethod
    def create_mandate(
        amount=200000,
        tenure=12,
        date=datetime.date(2020, 6, 1),
        authorization_code=None,
        customer=None,
    ):
        with transaction.atomic():
            if customer is None:
                customer = CustomerAppTest.create_corporate_customer()
            account_officer = StaffAppTest.create_account_officer()
            product = CommonAppTest.create_product(
                name="loan product", gateway_code="BG"
            )
            form_type = PipelineAppTest.create_form_type_mandate()

            # create rental form type
            PipelineAppTest.create_form_type_rental()
            mandate = Mandate.objects.create(
                customer=customer,
                product=product,
                account_officer=account_officer,
                tenure=tenure,
                initial_repayment_date=date,
                amount=amount,
                authorization_code=authorization_code,
                status=Mandate.ACTIVE,
            )

            review = MandateReview.objects.create(
                mandate=mandate,
                form_type=form_type,
                code=mandate.code,
                code_url=mandate.code_url,
                authorization_code=mandate.authorization_code,
            )

            for counter in range(0, tenure):
                collection_date = date
                month = ((collection_date.month + counter) % 12) + 1

                _, last_day = calendar.monthrange(collection_date.year, month)

                if collection_date.day > last_day:
                    collection_date = datetime.date(
                        collection_date.year, month, last_day
                    )
                else:
                    collection_date = datetime.date(
                        collection_date.year, month, collection_date.day
                    )

                Rental.objects.create(
                    mandate=mandate, collection_date=collection_date)

            review.foward()
            review.save()

            return mandate, review

    def test_fetch_payments(self):
        # create dummy mandates
        self.__create_dummy_mandates__()

        resp = cron.fetch_paystack_payments()
        self.assertEqual(resp, True)

    def test_confirm_payments(self):
        # create dummy mandates
        self.__create_dummy_mandates__()

        # create the queue with sample id 1493685
        queue = PaystackQueue.objects.create(status=True, batch_id=1493685)

        # fetch the batch response
        resp = cron.confirm_trials_status()
        self.assertEqual(resp, True)

    def test_mature_rentals(self):
        # create dummy mandates
        self.__create_dummy_mandates__()
        resp = cron.fail_paystack_payments()
        self.assertEqual(resp, True)

    def __create_dummy_mandates__(self):
        # create customers and mandates
        customers = []
        mandates = []

        with transaction.atomic():
            product = CommonAppTest.create_product(
                name="loan product", gateway_code="BG"
            )
            form_type = PipelineAppTest.create_form_type_mandate()

            email = "tripplecmati@sample.com"
            user = CustomerAppTest.create_customer(
                first_name=self.faker.first_name(),
                last_name=self.faker.last_name(),
                username=email.split("@")[0],
                email=email,
            )
            customer = Customer.objects.create(
                account_type=Customer.COPORATE_ACCOUNT,
                company_name=self.faker.company(),
                user=user,
                created_by=self.staff.user
            )
            customers.append(customer)
            mandate, review = TestUtilsMethods.create_mandate(
                amount=random.randint(10000000, 999999999),
                tenure=10,
                authorization_code="AUTH_z0v2ebhfcy",
                customer=customer
            )
            mandates.append(mandate)

            email = "sample@hemen.com"
            user = CustomerAppTest.create_customer(
                first_name=self.faker.first_name(),
                last_name=self.faker.last_name(),
                username=email.split("@")[0],
                email=email
            )
            customer = Customer.objects.create(
                account_type=Customer.COPORATE_ACCOUNT,
                company_name=self.faker.company(),
                user=user,
                created_by=self.staff.user
            )
            customers.append(customer)
            mandate, review = TestUtilsMethods.create_mandate(
                amount=random.randint(1000000000, 99999999999),
                tenure=10,
                authorization_code="AUTH_137cx2qchn",
                customer=customer,
            )
            mandates.append(mandate)

            email = "sabidacit@gmail.com"
            user = CustomerAppTest.create_customer(
                first_name=self.faker.first_name(),
                last_name=self.faker.last_name(),
                username=email.split("@")[0],
                email=email,
            )
            customer = Customer.objects.create(
                account_type=Customer.COPORATE_ACCOUNT,
                company_name=self.faker.company(),
                user=user,
                created_by=self.staff.user
            )
            customers.append(customer)
            mandate, review = TestUtilsMethods.create_mandate(
                amount=random.randint(10000000, 999999999),
                tenure=10,
                authorization_code="AUTH_nied9ihlg5",
                customer=customer,
            )
            mandates.append(mandate)
            return True, mandates, customers
        return False, mandates, customers
