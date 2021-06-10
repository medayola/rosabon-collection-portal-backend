import graphene
from graphene_django.types import DjangoObjectType

from common.models import Bank, Branch, Country, Department, Product, State


class BankType(DjangoObjectType):
    """
    DjangoObjectType for the Bank  Model
    """
    class Meta:
        model = Bank
        filter_fields = []
        interfaces = (graphene.relay.Node,)


class CountryType(DjangoObjectType):
    """
    DjangoObjectType for the Country Model
    """
    class Meta:
        model = Country
        filter_fields = []
        interfaces = (graphene.relay.Node,)


class StateType(DjangoObjectType):
    """
    DjangoObjectType for the State Model
    """
    class Meta:
        model = State
        filter_fields = []
        interfaces = (graphene.relay.Node,)


class DepartmentType(DjangoObjectType):
    """
    DjangoObjectModel representation of the model Department
    """

    class Meta:
        model = Department
        filter_fields = []
        interfaces = (graphene.relay.Node,)


class ProductType(DjangoObjectType):
    """
    DjangoObjectModel representation of the model Product
    """

    class Meta:
        model = Product
        filter_fields = []
        interfaces = (graphene.relay.Node,)


class BranchType(DjangoObjectType):
    """
    DjangoObjectModel representation of branch model
    """

    class Meta:
        model = Branch
        filter_fields = []
        interfaces = (graphene.relay.Node,)
