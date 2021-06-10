import graphene
from django.db import transaction
from graphql.error import GraphQLError
from graphql_relay import from_global_id

from common.graphql.inputs import BankInput, CountryInput
from common.graphql.types import (BankType, BranchType, CountryType,
                                  DepartmentType, ProductType)
from common.models import Bank, Branch, Country, Department, Product
from staff.models import Staff


# Bank Mutations
#   - Create Bank
class CreateBank(graphene.Mutation):
    class Arguments:
        input = BankInput(required=True)

    ok = graphene.Boolean()
    bank = graphene.Field(BankType)

    @staticmethod
    def mutate(root, info, input=None):
        ok = True

        bank = Bank.objects.filter(
            name=input.name).first()

        if bank:
            raise GraphQLError(
                'bank already exists! with name {}'.format(input.name))

        bank = Bank.objects.filter(
            abbreviation=input.abbreviation).first()

        if bank:
            raise GraphQLError(
                'bank already exists! with abbreviation {}'.format(
                    input.abbreviation
                )
            )

        try:
            bank_instance = Bank(
                name=input.name,
                abbreviation=input.abbreviation
            )
            bank_instance.save()
        except Exception:
            raise GraphQLError('An Error Occured while saving bank!')
        return CreateBank(ok=ok, bank=bank_instance)


#   - Update Bank
class UpdateBank(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = BankInput(required=True)

    ok = graphene.Boolean()
    bank = graphene.Field(BankType)

    @staticmethod
    def mutate(root, info, **input):
        ok = False
        try:
            _, id = from_global_id(input.get('id'))
            bank_instance = Bank.objects.get(id=id)
        except Exception:
            raise GraphQLError('invalid bank selected!')
        input = input.get('input')
        if bank_instance:
            ok = True
            bank_instance.name = input.get('name', bank_instance.name)
            bank_instance.abbreviation = input.get(
                'abbreviation', bank_instance.abbreviation)
            bank_instance.save()
            return UpdateBank(ok=ok, bank=bank_instance)
        return UpdateBank(ok=ok, bank=None)


# Country Mutations
# - Create Country
class CreateCountry(graphene.Mutation):
    class Arguments:
        input = CountryInput(required=True)

    ok = graphene.Boolean()
    country = graphene.Field(CountryType)

    @staticmethod
    def mutate(root, info, input=None):
        ok = True
        country_instance = Country(
            name=input.name,
            abbreviation=input.abbreviation
        )
        country_instance.save()
        return CreateCountry(ok=ok, country=country_instance)


# - Update Country
class UpdateCountry(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = CountryInput(required=True)

    ok = graphene.Boolean(required=True)
    country = graphene.Field(CountryType)

    @staticmethod
    def mutate(root, info, **input):
        ok = False
        try:
            _, id = from_global_id(input.get('id'))
        except Exception:
            raise GraphQLError('invalid country selected!')
        country_instance = Country.objects.get(pk=id)
        input = input.get('input')
        if country_instance:
            ok = True
            country_instance.name = input.get('name', country_instance.name)
            country_instance.abbreviation = input.get(
                'abbreviation', country_instance.abbreviation)
            country_instance.save()
            return UpdateCountry(ok=ok, country=country_instance)

        return UpdateBank(ok=ok, country=None)


# Department Mutations
# create
class CreateDepartment(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        head = graphene.ID()

    success = graphene.Boolean(required=True)
    department = graphene.Field(DepartmentType)

    @staticmethod
    def mutate(root, info, **input):
        __department__ = Department()
        __department__.name = input.get('name', '')

        try:
            _, __head_of_department__ = from_global_id(input.get('head'))
            __head_of_department__ = Staff.objects.filter(
                pk=__head_of_department__).first()
        except Exception:
            __head_of_department__ = None

        if __head_of_department__ is not None:
            __department__.head = __head_of_department__

        __department__.save()
        return CreateDepartment(success=True, department=__department__)


class UpdateDepartment(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String(required=True)
        head = graphene.ID()

    success = graphene.Boolean(required=True)
    department = graphene.Field(DepartmentType)

    @staticmethod
    def mutate(root, info, **input):
        _, __department__ = from_global_id(input.get('id'))
        __department__ = Department.objects.filter(pk=__department__).first()
        if __department__:
            __department__.name = input.get('name')

            try:
                _, __head_of_department__ = from_global_id(input.get('head'))
                __head_of_department__ = Staff.objects.filter(
                    pk=__head_of_department__).first()
            except Exception:
                __head_of_department__ = None

            if __head_of_department__ is not None:
                __department__.head = __head_of_department__
            else:
                __department__.head = __department__.head

        else:
            raise GraphQLError('invalid department!')

        return UpdateDepartment(success=True, department=__department__)

# Product Mutations
# create


class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        gateway_code = graphene.String(required=False)

    id = graphene.ID()
    success = graphene.Boolean(required=True)
    product = graphene.Field(ProductType)

    @staticmethod
    def mutate(root, info, **input):
        with transaction.atomic():
            product = Product()
            product.name = input.get('name', '')
            product.gateway_code = input.get('gateway_code', '')
            product.save()
            return CreateProduct(success=True, id=product.id, product=product)
        return CreateProduct(success=False, id=None, product=None)


class UpdateProduct(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String(required=True)
        head = graphene.ID()

    success = graphene.Boolean(required=True)
    product = graphene.Field(ProductType)

    @staticmethod
    def mutate(root, info, **input):
        with transaction.atomic():
            _, id = from_global_id(input.get('id', ''))
            product = Product.objects.get(id=id)
            product.name = input.get('name', product.name)
            product.gateway_code = input.get(
                'gateway_code', product.gateway_code)
            product.save()
            return UpdateProduct(success=True, product=product)
        return UpdateProduct(success=False, product=None)


class CreateBranch(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)

    success = graphene.Boolean(required=True)
    branch = graphene.Field(BranchType)

    @staticmethod
    def mutate(root, info, **input):
        try:
            return CreateBranch(
                success=True,
                branch=Branch.objects.create(
                    name=input.get('name')
                ))
        except Exception:
            return CreateBranch(success=False, branch=Branch.objects.none())


class UpdateBranch(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String(required=True)

    success = graphene.Boolean(required=True)
    branch = graphene.Field(BranchType)

    @staticmethod
    def mutate(root, info, **input):
        try:
            instance = Branch.objects.get(id=input.get('id'))
            instance.name = input.get('name', instance.name)
            instance.save()
            return UpdateBranch(success=True, branch=instance)
        except Exception:
            return UpdateBranch(success=False, branch=Branch.objects.none())


class DeleteBranch(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean(required=True)

    @staticmethod
    def mutate(root, info, **input):
        try:
            instance = Branch.objects.get(id=input.get('id'))
            instance.delete()
            return UpdateBranch(success=True)
        except Exception:
            return UpdateBranch(success=False)


class Mutation(graphene.ObjectType):

    create_bank = CreateBank.Field()
    create_department = CreateDepartment.Field()
    create_country = CreateCountry.Field()
    create_product = CreateProduct.Field()

    update_country = UpdateCountry.Field()
    update_bank = UpdateBank.Field()
    update_department = UpdateDepartment.Field()
    update_product = UpdateProduct.Field()
