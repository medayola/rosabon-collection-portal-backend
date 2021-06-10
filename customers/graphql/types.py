import graphene
from graphene import ObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType

from customers.models import BankingDetail, Customer
from mandates.graphql.types import MandateType
from mandates.models import Mandate
from utils.formatters import Formatters


class AccountType(ObjectType):
    """
    ObjectType representing Account types 
    """
    id = graphene.String()
    name = graphene.String()

    def resolve_name(self, info):
        return '{} Account'.format(self['name'])


class CustomerType(DjangoObjectType):
    """
    DjangoObjectType for the Customer Model
    """

    name = graphene.String()
    email = graphene.String()
    firstname = graphene.String()
    lastname = graphene.String()
    mandates_count = graphene.Int()
    account_type = graphene.String()
    gender = graphene.String()
    sorted_mandates = DjangoFilterConnectionField(MandateType)

    class Meta:
        model = Customer
        filter_fields = []
        interfaces = (graphene.relay.Node,)

    def resolve_account_type(self, info):
        return f'{self.account_type}'

    def resolve_sorted_mandates(self, info):
        return self.mandates.filter(is_deleted=False).exclude(status=Mandate.PENDING).order_by('-id')

    def resolve_name(self, info):
        return self.fullname()

    def resolve_firstname(self, info):
        return '{}'.format(
            self.user.first_name
        )

    def resolve_lastname(self, info):
        return '{}'.format(
            self.user.last_name
        )

    def resolve_email(self, info):
        return '{}'.format(
            self.user.email
        )

    def resolve_mandates_count(self, info):
        return self.mandates.count()

    def resolve_gender(self, info):
        gender = self.gender
        return gender


class BankDetailType(DjangoObjectType):
    """
    DjangoObjectType for the BankDetail Model
    """
    formatted_account_number = graphene.String()

    class Meta:
        model = BankingDetail
        filter_fields = []
        interfaces = (graphene.relay.Node,)

    def resolve_formatted_account_number(self, info):
        return Formatters.split_account_number(self.account_number)
