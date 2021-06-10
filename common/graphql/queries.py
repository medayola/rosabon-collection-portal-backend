import graphene
from graphene_django.filter import DjangoFilterConnectionField

from common.graphql.types import (BankType, BranchType, CountryType,
                                  DepartmentType, ProductType, StateType)
from common.models import Bank, Country, Department, Product, State, Branch


class Query(graphene.ObjectType):
    country = graphene.relay.Node.Field(CountryType)
    state = graphene.relay.Node.Field(StateType)
    bank = graphene.relay.Node.Field(BankType)
    product = graphene.relay.Node.Field(ProductType)
    department = graphene.relay.Node.Field(DepartmentType)
    branch = graphene.relay.Node.Field(BranchType)

    countries = DjangoFilterConnectionField(CountryType)
    states = DjangoFilterConnectionField(StateType)
    banks = DjangoFilterConnectionField(BankType)
    products = DjangoFilterConnectionField(ProductType)
    departments = DjangoFilterConnectionField(DepartmentType)
    branches = DjangoFilterConnectionField(BranchType)

    def resolve_bank(self, instance, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Bank.objects.filter(pk=id, is_deleted=False).first()
        return None

    def resolve_state(self, instance, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return State.objects.filter(pk=id, is_deleted=False).first()
        return None

    def resolve_country(self, instance, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Country.objects.filter(pk=id, is_deleted=False).first()
        return None

    def resolve_department(self, info, **kwargs):
        id = kwargs.get('id', None)

        if id is not None:
            return Department.objects.filter(id=id, is_deleted=False).first()
        else:
            return None

    def resolve_product(self, info, **kwargs):
        id = kwargs.get('id', None)

        if id is not None:
            return Product.objects.filter(id=id, is_deleted=False).first()
        else:
            return None

    def resolve_branch(self, info, **kwargs):
        id = kwargs.get('id', None)

        if id is not None:
            return Branch.objects.filter(id=id, is_deleted=False).first()
        else:
            return Branch.objects.none()

    def resolve_products(self, info):
        return Product.objects.filter(is_deleted=False)

    def resolve_departments(self, info):
        return Department.objects.filter(is_deleted=False)

    def resolve_countries(self, instance, **kwargs):
        return Country.objects.filter(is_deleted=False)

    def resolve_states(self, instance, **kwargs):
        return State.objects.filter(is_deleted=False)

    def resolve_banks(self, instance, **kwargs):
        return Bank.objects.filter(is_deleted=False)

    def resolve_branches(self, instance, **kwargs):
        return Branch.objects.filter(is_deleted=False)
