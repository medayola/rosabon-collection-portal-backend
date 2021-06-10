from django.contrib.auth import get_user_model
from django.test import TestCase
from graphene.test import Client
from graphql_relay import to_global_id
import numpy as np
import time

from customers.graphql.types import BankDetailType, CustomerType
from customers.models import BankingDetail, Customer
from users.models import Person
from common.models import Bank
from paystackcollection.schema import schema
from staff.tests.test_graphql import StaffAppTest

from faker import Faker
from users.tests.test_graphql import MockUser


class CustomerAppTest(TestCase):
    @staticmethod
    def create_bank(name="bank", abbreviation="b"):
        bank = Bank.objects.create(name=name, abbreviation=abbreviation)
        return bank

    @staticmethod
    def create_customer(
        first_name="",
        last_name="",
        email=None,
        username=f"username{time.time()}",
        password="passw0rd1o1",
    ):
        user = get_user_model().objects.create(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password,
        )
        if email:
            user.email = email
            user.save()
        return user

    @staticmethod
    def create_personal_customer(first_name="surname", last_name="othernames"):
        user = CustomerAppTest.create_customer(
            first_name=first_name, last_name=last_name
        )
        return Customer.objects.create(
            user=user,
            account_type=Customer.PERSONAL_ACCOUNT,
            gender="M",
            person_type=Person.CUSTOMER,
            created_by=StaffAppTest.create_account_officer().user
        )

    @staticmethod
    def create_corporate_customer():
        faker = Faker()
        name = faker.company()
        names = name.split(" ")
        email = faker.safe_email()

        if len(names) == 1:
            surname = name.replace(",", "")
            othernames = name.replace(",", "")
        elif len(names) > 1:
            surname = names[0].replace(",", "")
            othernames = " ".join(
                map(lambda name: name.replace(",", ""), names[1:]))

        user = CustomerAppTest.create_customer(
            first_name=surname, last_name=othernames, username=email.split(
                "@")[0]
        )
        return Customer.objects.create(
            user=user,
            account_type=Customer.COPORATE_ACCOUNT,
            gender=Person.MALE,
            person_type=Person.CUSTOMER,
            company_name=name,
            created_by=StaffAppTest.create_account_officer().user
        )

    @staticmethod
    def create_banking_detail(account_number):
        faker = Faker()
        customer = CustomerAppTest.create_customer(
            first_name=faker.first_name(), last_name=faker.last_name()
        )
        bank = CustomerAppTest.create_bank(name="bank", abbreviation="b")
        return BankingDetail.objects.create(
            customer=customer, bank=bank, account_number=account_number
        )

    def setUp(self):
        self.client = Client(schema=schema)
        self.staff = StaffAppTest.create_staff()
        self.faker = Faker()

    def test_can_create_corporate_customer(self):
        bank = CustomerAppTest.create_bank()

        query = """
            mutation CreateCustomer (
                $accountNumber:String!,
                $accountType:String!,
                $bank:ID!,
                $companyName:String,
                $email:String!,
                $gender:String!,
                $identificationPin:String!,
                $othernames:String,
                $phoneNumber:String!,
                $surname:String
                ) {
                createCustomer(
                    accountNumber:$accountNumber,
                    accountType:$accountType,
                    bank:$bank,
                    companyName:$companyName,
                    email:$email,
                    gender:$gender,
                    identificationPin:$identificationPin,
                    othernames:$othernames,
                    phoneNumber:$phoneNumber,
                    surname:$surname
                ) {
                    success
                }
            }
        """

        executed = self.client.execute(
            query,
            context_value=MockUser(self.staff.user),
            variable_values={
                "accountNumber": "00000000",
                "accountType": Customer.COPORATE_ACCOUNT,
                "bank": to_global_id("BankType", bank.id),
                "companyName": "DANGOTE LTD",
                "email": "sample@example.net",
                "gender": Person.MALE,
                "identificationPin": "0001110",
                "phoneNumber": "09020373748",
            },
        )

        self.assertEqual({"success": True}, executed["data"]["createCustomer"])

    def test_can_update_corporate_customer(self):
        customer = CustomerAppTest.create_corporate_customer()
        bank = CustomerAppTest.create_bank(
            name="union bank", abbreviation="ub")
        query = """
            mutation UpdateCustomer (
                $id:ID!,
                $accountNumber:String,
                $accountType:String,
                $bank:ID,
                $companyName:String,
                $email:String,
                $gender:String,
                $identificationPin:String,
                $othernames:String,
                $phoneNumber:String,
                $surname:String
                ) {
                updateCustomer(
                    id:$id,
                    accountNumber:$accountNumber,
                    accountType:$accountType,
                    bank:$bank,
                    companyName:$companyName,
                    email:$email,
                    gender:$gender,
                    identificationPin:$identificationPin,
                    othernames:$othernames,
                    phoneNumber:$phoneNumber,
                    surname:$surname
                ) {
                    success
                    customer {
                        bankDetail {
                            accountNumber
                            bank {
                                id
                            }
                        }
                        user {
                            lastName
                            firstName
                        }
                        identificationPin
                    }
                }
            }
        """

        executed = self.client.execute(
            query,
            context_value=MockUser(self.staff.user),
            variable_values={
                "id": to_global_id("CustomerType", customer.id),
                "accountNumber": "0000002220",
                "bank": to_global_id("BankType", bank.id),
                "identificationPin": "0001110",
                "othernames": "loius",
                "surname": "edet",
            },
        )

        self.assertEqual(
            {
                "success": True,
                "customer": {
                    "bankDetail": {
                        "accountNumber": "0000002220",
                        "bank": {"id": to_global_id("BankType", bank.id), },
                    },
                    "user": {"lastName": "loius", "firstName": "edet"},
                    "identificationPin": "0001110",
                },
            },
            executed["data"]["updateCustomer"],
        )

    def test_can_view_corporate_customer(self):
        customer = CustomerAppTest.create_corporate_customer()
        query = """
            query Customer ($id:ID!) {
                customer (id:$id) {
                    user {
                        firstName
                        lastName
                    }
                }
            }
        """
        executed = self.client.execute(
            query, context_value=MockUser(self.staff.user), variable_values={
                "id": to_global_id("CustomerType", customer.id)}
        )
        self.assertEqual(
            {
                "user": {
                    "firstName": customer.user.first_name,
                    "lastName": customer.user.last_name,
                }
            },
            executed["data"]["customer"],
        )

    def test_can_create_personal_customer(self):
        bank = CustomerAppTest.create_bank(
            name="first bank", abbreviation="fbn")

        query = """
            mutation CreateCustomer (
                $accountNumber:String!,
                $accountType:String!,
                $bank:ID!,
                $companyName:String,
                $email:String!,
                $gender:String!,
                $identificationPin:String!,
                $othernames:String,
                $phoneNumber:String!,
                $surname:String
                ) {
                createCustomer(
                    accountNumber:$accountNumber,
                    accountType:$accountType,
                    bank:$bank,
                    companyName:$companyName,
                    email:$email,
                    gender:$gender,
                    identificationPin:$identificationPin,
                    othernames:$othernames,
                    phoneNumber:$phoneNumber,
                    surname:$surname
                ) {
                    success
                }
            }
        """

        executed = self.client.execute(
            query,
            context_value=MockUser(self.staff.user),
            variable_values={
                "accountNumber": "00000000",
                "accountType": Customer.PERSONAL_ACCOUNT,
                "bank": to_global_id("BankType", bank.id),
                "email": "sample@example.net",
                "gender": Person.MALE,
                "identificationPin": "0001110",
                "othernames": "ali tambuwal",
                "phoneNumber": "09020373748",
                "surname": "surname",
            },
        )

        self.assertEqual({"success": True}, executed["data"]["createCustomer"])

    def test_can_update_personal_customer(self):
        customer = CustomerAppTest.create_personal_customer()
        bank = CustomerAppTest.create_bank(
            name="union bank", abbreviation="ub")
        query = """
            mutation UpdateCustomer (
                $id:ID!,
                $accountNumber:String,
                $accountType:String,
                $bank:ID,
                $companyName:String,
                $email:String,
                $gender:String,
                $identificationPin:String,
                $othernames:String,
                $phoneNumber:String,
                $surname:String
                ) {
                updateCustomer(
                    id:$id,
                    accountNumber:$accountNumber,
                    accountType:$accountType,
                    bank:$bank,
                    companyName:$companyName,
                    email:$email,
                    gender:$gender,
                    identificationPin:$identificationPin,
                    othernames:$othernames,
                    phoneNumber:$phoneNumber,
                    surname:$surname
                ) {
                    success
                    customer {
                        bankDetail {
                            accountNumber
                            bank {
                                id
                            }
                        }
                        user {
                            lastName
                            firstName
                        }
                        identificationPin
                    }
                }
            }
        """

        executed = self.client.execute(
            query,
            context_value=MockUser(self.staff.user),
            variable_values={
                "id": to_global_id("CustomerType", customer.id),
                "accountNumber": "0000002220",
                "bank": to_global_id("BankType", bank.id),
                "identificationPin": "0001110",
                "othernames": "loius",
                "surname": "edet",
            },
        )

        self.assertEqual(
            {
                "success": True,
                "customer": {
                    "bankDetail": {
                        "accountNumber": "0000002220",
                        "bank": {"id": to_global_id("BankType", bank.id), },
                    },
                    "user": {"lastName": "loius", "firstName": "edet"},
                    "identificationPin": "0001110",
                },
            },
            executed["data"]["updateCustomer"],
        )

    def test_can_view_personal_customer(self):
        customer = CustomerAppTest.create_personal_customer(
            first_name="limo", last_name="came"
        )
        query = """
            query Customer ($id:ID!) {
                customer (id:$id) {
                    user {
                        firstName
                        lastName
                    }
                }
            }
        """
        executed = self.client.execute(
            query, context_value=MockUser(self.staff.user), variable_values={
                "id": to_global_id("CustomerType", customer.id)}
        )
        self.assertEqual(
            {
                "user": {
                    "firstName": customer.user.first_name,
                    "lastName": customer.user.last_name,
                }
            },
            executed["data"]["customer"],
        )
        pass

    def test_can_view_corporate_customer(self):
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()

        customer = CustomerAppTest.create_personal_customer(
            first_name=first_name, last_name=last_name
        )

        query = """
            query Customer ($id:ID!) {
                customer (id:$id) {
                    user {
                        firstName
                        lastName
                    }
                }
            }
        """
        executed = self.client.execute(
            query, context_value=MockUser(self.staff.user), variable_values={
                "id": to_global_id("CustomerType", customer.id)}
        )
        self.assertEqual(
            {
                "user": {
                    "firstName": customer.user.first_name,
                    "lastName": customer.user.last_name,
                }
            },
            executed["data"]["customer"],
        )

    def test_can_view_customers(self):
        customer = CustomerAppTest.create_personal_customer(
            first_name="dangote", last_name="aliko"
        )
        customers = [customer]
        query = """
            query Customer ($id:ID!) {
                customer (id:$id) {
                    user {
                        firstName
                        lastName
                    }
                }
            }
        """

        executed = self.client.execute(
            query, context_value=MockUser(self.staff.user),
            variable_values={
                "id": to_global_id("CustomerType", customer.id)}
        )
        self.assertEqual(
            {
                "user": {
                    "firstName": customer.user.first_name,
                    "lastName": customer.user.last_name,
                }
            },
            executed["data"]["customer"],
        )
