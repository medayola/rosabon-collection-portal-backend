import graphene

from django.contrib.auth.models import User
from django.db import transaction
from graphql.error import GraphQLError
from graphql_relay import from_global_id

from common.models import Bank
from customers.graphql.types import CustomerType
from customers.models import BankingDetail
from customers.models import Customer
from users.models import Person
from staff.models import Staff


# Customer Mutations
#   - Create Customer Mutation
class CreateCustomer(graphene.Mutation):
    class Arguments:
        account_officer = graphene.String(required=True)
        account_number = graphene.String(required=True)
        bank = graphene.ID(required=True)
        branch = graphene.ID(required=True)
        surname = graphene.String()
        othernames = graphene.String()
        email = graphene.String(required=True)
        phone_number = graphene.String(required=True)
        gender = graphene.String()
        identification_pin = graphene.String()
        account_type = graphene.String(required=True)
        company_name = graphene.String()

    id = graphene.ID(required=True)
    success = graphene.Boolean(required=True)
    message = graphene.String(required=True)

    @staticmethod
    def mutate(root, info, **input):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You are not Logged In')

        # clean the input
        __account_number__ = input.get("account_number", "")

        # get the bank
        _, __bank__ = from_global_id(input.get("bank", ""))
        try:
            __bank__ = Bank.objects.get(id=__bank__)
        except Exception:
            raise GraphQLError("Unrecognized Bank Selected!")

        # get the gender
        gender = input.get("gender")

        with transaction.atomic():
            # collect the account type
            account_type = input.get("account_type", Customer.PERSONAL_ACCOUNT)
            # check if the customer is a coporate or personal
            # if it is a coporate account collect the company name
            company_name = ""
            if account_type == Customer.COPORATE_ACCOUNT:
                company_name = input.get("company_name")

                if not company_name:
                    raise GraphQLError("Company Name is required!")

                names = company_name.split(" ")
                if len(names) == 1:
                    surname = company_name
                    othernames = company_name
                elif len(names) > 1:
                    surname = names[0]
                    othernames = " ".join(names[1:])
                gender = Person.COPORATE

            elif account_type == Customer.PERSONAL_ACCOUNT:
                surname = input.get("surname")
                othernames = input.get("othernames")

                if not surname:
                    raise GraphQLError("Surname is required!")
                if not othernames:
                    raise GraphQLError("The Other Names Feild is required!")

            gender = input.get("gender")
            if gender == '':
                gender = Person.COPORATE

            # get the account officer
            try:
                officer = Staff.objects.filter(
                    user__id=input.get('account_officer'),
                    is_account_officer=True
                ).first()
            except Exception:
                raise GraphQLError('Unknown Account officer selected!')

            # create the user instance
            __user__ = User()
            __user__.username = input.get("email").split("@")[0]
            __user__.first_name = surname
            __user__.last_name = othernames
            __user__.email = input.get("email")
            __user__.set_password(__user__.username)
            __user__.save()

            __customer__ = Customer()
            __customer__.user = __user__
            __customer__.tel = input.get("phone_number", "")
            __customer__.gender = gender
            __customer__.person_type = Person.CUSTOMER
            __customer__.account_type = account_type
            if company_name:
                __customer__.company_name = company_name
            __customer__.active = False
            __customer__.identification_pin = input.get(
                "identification_pin", "")
            __customer__.underwriter = user
            __customer__.created_by = officer.user
            __customer__.save()

            # create banking detail and move to the model as a signal
            BankingDetail.objects.create(
                customer=__customer__,
                bank=__bank__,
                account_number=__account_number__
            )

            return CreateCustomer(
                success=True,
                id=__customer__.id,
                message="{} successfully added!".format(__customer__.name()),
            )
        return CreateCustomer(
            success=False,
            id=None,
            message="An erorr occured while creating Customer!"
        )


#   - Update Customer Mutation
class UpdateCustomer(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        account_number = graphene.String()
        bank = graphene.ID()
        surname = graphene.String()
        othernames = graphene.String()
        email = graphene.String()
        phone_number = graphene.String()
        gender = graphene.String()
        identification_pin = graphene.String()
        account_type = graphene.String()
        company_name = graphene.String()

    success = graphene.Boolean(required=True)
    customer = graphene.Field(CustomerType)

    @staticmethod
    def mutate(root, info, **input):
        # clean the input
        _, __user__ = from_global_id(input.get("id"))
        __user__ = Customer.objects.filter(pk=__user__).first().user

        if __user__:
            with transaction.atomic():
                company_name = ""
                account_type = input.get(
                    "account_type", Customer.PERSONAL_ACCOUNT)
                if account_type == Customer.COPORATE_ACCOUNT:
                    company_name = input.get("company_name")

                    if not company_name:
                        raise GraphQLError("Company Name is required!")

                    names = company_name.split(" ")
                    if len(names) == 1:
                        surname = company_name
                        othernames = company_name
                    elif len(names) > 1:
                        surname = names[0]
                        othernames = " ".join(names[1:])

                elif account_type == Customer.PERSONAL_ACCOUNT:
                    surname = input.get("surname", __user__.first_name)
                    othernames = input.get("othernames", __user__.last_name)

                    if not surname:
                        raise GraphQLError("Surname is required!")
                    if not othernames:
                        raise GraphQLError(
                            "The Other Names Feild is required!")

                # create the user instance
                email = input.get("email", __user__.email)
                username = __user__.username
                if email:
                    username = email.split("@")[0]

                __user__.username = username
                __user__.first_name = surname
                __user__.last_name = othernames
                __user__.email = email
                __user__.save()

                __customer__ = __user__.customer
                __customer__.gender = input.get("gender", __customer__.gender)
                __customer__.person_type = Person.CUSTOMER
                __customer__.account_type = input.get(
                    "account_type", __customer__.account_type
                )
                __customer__.identification_pin = input.get(
                    "identification_pin", __customer__.identification_pin
                )

                _, bank = from_global_id(input.get("bank"))
                bank = Bank.objects.filter(pk=bank).first()
                account_number = input.get("account_number", None)
                bank_detail = BankingDetail.objects.filter(
                    customer=__customer__
                ).first()

                if not bank_detail:
                    bank_detail = BankingDetail(customer=__customer__)
                    if not bank:
                        bank = bank_detail.bank
                    if not account_number:
                        account_number = bank_detail.account_number

                bank_detail.bank = bank
                bank_detail.account_number = account_number
                bank_detail.save()

                # check if the customer is a coporate or personal
                # if it is a coporate account collect the company name
                if __customer__.account_type == Customer.COPORATE_ACCOUNT:
                    company_name = input.get(
                        "company_name", __customer__.company_name)
                    if company_name:
                        __customer__.company_name = company_name
                    else:
                        raise GraphQLError("Company Name is required!")
                __customer__.save()
                return UpdateCustomer(success=True, customer=__customer__)
        else:
            raise GraphQLError("Invalid user id!")
        return UpdateCustomer(success=False, customer=None)


class DeleteCustomer(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean(required=True)

    @staticmethod
    def mutate(root, info, **input):
        _, __user__ = from_global_id(input.get("id"))
        __user__ = User.objects.filter(pk=__user__).first()
        if __user__:
            __user__.customer.is_deleted = True
            __user__.customer.save()
            return DeleteCustomer(success=True)
        else:
            raise GraphQLError("Invalid customer id!")
        return DeleteCustomer(success=True)


class GetCustomerByEmail(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)

    id = graphene.ID()
    name = graphene.String()
    success = graphene.Boolean(required=True)

    @staticmethod
    def mutate(root, info, **input):
        try:
            __customer__ = Customer.objects.get(
                user__email=input.get("email", ""))
            return GetCustomerByEmail(
                id=__customer__.user.id, name=__customer__.fullname(),
                success=True
            )
        except Customer.DoesNotExist:
            raise GraphQLError(
                "No Customer exists with email address: {}".format(
                    input.get("email", "")
                )
            )


class Mutation(graphene.ObjectType):
    createCustomer = CreateCustomer.Field()
    update_customer = UpdateCustomer.Field()
    delete_customer = DeleteCustomer.Field()

    get_customer_by_email = GetCustomerByEmail.Field()
