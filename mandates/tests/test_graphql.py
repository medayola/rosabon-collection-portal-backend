import calendar
import datetime

from django.db import transaction
from django.test import TestCase
from faker import Faker
from graphene.test import Client
from graphql_relay import to_global_id

from common.tests.test_graphql import CommonAppTest
from customers.tests.test_graphql import CustomerAppTest
from mandates.models import Mandate, Rental, Trial
from paystackcollection.schema import schema
from pipeline.models import FormType, MandateReview
from pipeline.tests.test_graphql import PipelineAppTest
from staff.tests.test_graphql import StaffAppTest
from users.tests.test_graphql import MockUser, UserAppTest


class MandateAppTest(TestCase):

    @staticmethod
    def create_mandate(amount=200000, tenure=12, date=datetime.date(2020, 1, 1)):
        with transaction.atomic():
            customer = CustomerAppTest.create_corporate_customer()
            account_officer = StaffAppTest.create_account_officer()
            product = CommonAppTest.create_product(
                name="loan product", gateway_code="BG")
            form_type = PipelineAppTest.create_form_type_mandate()
            # form_type = form_type.objects.filter(name=FormType.MANDATE)

            # create rental form type
            PipelineAppTest.create_form_type_rental()
            mandate = Mandate.objects.create(
                customer=customer,
                product=product,
                account_officer=account_officer,
                tenure=tenure,
                initial_repayment_date=date,
                amount=amount
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

                _, last_day = calendar.monthrange(
                    collection_date.year, month)

                if collection_date.day > last_day:
                    collection_date = datetime.date(
                        collection_date.year, month, last_day)
                else:
                    collection_date = datetime.date(
                        collection_date.year, month, collection_date.day)

                Rental.objects.create(
                    mandate=mandate,
                    collection_date=collection_date)

            review.foward()
            review.save()

            return mandate, review

    @staticmethod
    def create_trial(
            collection_date=datetime.date(2020, 3, 1),
            date=datetime.date(2020, 2, 1),
            tenure=10,
            amount=100000):
        rental = create_rental(collection_date=collection_date,
                               date=date, tenure=tenure, amount=amount)
        message = 'rental created!'
        return Trial.objects.create(rental=rental, message=message)

    @staticmethod
    def create_rental(
            collection_date=datetime.date(2020, 3, 1),
            date=datetime.date(2020, 2, 1),
            tenure=10,
            amount=100000):
        mandate = create_mandate(tenure=tenure, date=date, amount=amount)
        return Rental.objects.create(mandate=mandate, collection_date=collection_date)

    def setUp(self):
        self.client = Client(schema=schema)
        self.staff = StaffAppTest.create_staff()
        self.faker = Faker()

    def test_can_create_mandate(self):
        customer = CustomerAppTest.create_corporate_customer()
        account_officer = StaffAppTest.create_account_officer()
        product = CommonAppTest.create_product(
            name="loan product", gateway_code="BG")
        form_type = PipelineAppTest.create_form_type_mandate()

        query = '''
            mutation CreateMandate(
                $id: ID,
                $customer: ID!,
                $code: String,
                $tenure: Int!,
                $initialRepaymentDate: String!,
                $rentals: [String]!
                $paymentOption: String!,
                $accountOfficer: ID!,
                $amount: String!,
                $currentStage:ID,
                $formType:ID,
                $product:ID!,
                $isActive:Boolean!
                ) {
                mandateMutation(
                    id: $id,
                    customer: $customer,
                    code: $code,
                    tenure:$tenure,
                    rentals:$rentals,
                    initialRepaymentDate:$initialRepaymentDate,
                    paymentOption: $paymentOption,
                    accountOfficer: $accountOfficer,
                    amount: $amount,
                    currentStage:$currentStage,
                    formType:$formType,
                    product:$product
                    isActive:$isActive
                ) {
                    success
                    mandate {
                        paymentOption
                        product {
                            id
                        }
                    }
                }
            }
        '''

        executed = self.client.execute(
            query,
            context_value=MockUser(self.staff.user),
            variable_values={
                "id": "",
                "customer": customer.user.id,
                "formType": to_global_id("FormType", form_type.id),
                "code": "000002",
                "tenure": "15",
                "rentals": [],
                "initialRepaymentDate": datetime.date(2020, 1, 1),
                "paymentOption": Mandate.PAYSTACK,
                "accountOfficer": account_officer.user.id,
                "amount": 10000000,
                "product": to_global_id("ProductType", product.id),
                "isActive": True
            })

        self.assertEqual({
            "success": True,
            "mandate": {
                "paymentOption": Mandate.PAYSTACK,
                "product": {
                    "id": to_global_id("ProductType", product.id)
                }
            }
        }, executed['data']['mandateMutation'])

    def test_can_view_mandate(self):
        mandate, review = MandateAppTest.create_mandate(
            amount=1000000, tenure=8)
        query = '''
            query GetMandate(
                $id: ID!
                ) {
                    mandate(id: $id) {
                        id
                        status
                        tenure
                        initialRepaymentDate
                    }
                }
        '''

        executed = self.client.execute(
            query,
            context_value=MockUser(self.staff.user),
            variable_values={
                "id": to_global_id("MandateType", mandate.id)
            })
        self.assertEqual({
            "id": to_global_id("MandateType", mandate.id),
            "status": mandate.status,
            "tenure": mandate.tenure,
            "initialRepaymentDate": datetime.datetime.strftime(
                mandate.initial_repayment_date, "%Y-%m-%d")
        }, executed['data']['mandate'])

    def test_can_update_mandate(self):
        mandate, review = MandateAppTest.create_mandate(
            amount=1500000, tenure=6)
        query = '''
            mutation ReviewMandate(
                $id: ID!,
                $comment: String!,
                $status: Boolean!) {
                    reviewMandate(
                        id: $id,
                        comment: $comment,
                        status: $status) {
                            success
                        }
                    }
        '''

        executed = self.client.execute(
            query,
            context_value=MockUser(self.staff.user),
            variable_values={
                "id": to_global_id("MandateReviewType", review.id),
                "comment": self.faker.sentence(),
                "status": True,
            })
        self.assertEqual({
            "success": True
        }, executed['data']['reviewMandate'])

    def test_can_convert_rental_to_manual(self):
        mandate, review = MandateAppTest.create_mandate(
            amount=15000000, tenure=5)
        rentals = mandate.rentals.order_by('collection_date')[:2]

        query = '''
            mutation ConvertRentalToManual (
                $id: ID!,
                $rentals:[ID]!) {
                convertToManual(
                    id: $id,
                    rentals: $rentals) {
                        success
                        response {
                            mandate{
                                id
                            }
                        }
                    }
                }
        '''

        executed = self.client.execute(
            query,
            context_value=MockUser(self.staff.user),
            variable_values={
                "id": to_global_id("MandateType", mandate.id),
                "rentals": [to_global_id("RentalType", rental.id) for rental in rentals]
            })
        self.assertEqual({
            "success": True,
            "response": {
                "mandate": {
                    "id": to_global_id("MandateType", mandate.id)
                }
            }
        }, executed['data']['convertToManual'])
