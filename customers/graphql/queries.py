import graphene
from graphql.error import GraphQLError
from graphene_django.filter import DjangoFilterConnectionField
from django.db.models import Q

from customers.graphql.filters import CustomerFilter
from customers.graphql.types import AccountType, CustomerType
from customers.models import Customer


class Query(graphene.ObjectType):

    customer = graphene.relay.Node.Field(CustomerType)
    customers = DjangoFilterConnectionField(
        CustomerType, filterset_class=CustomerFilter)

    my_customer = graphene.relay.Node.Field(CustomerType)
    my_customers = DjangoFilterConnectionField(
        CustomerType, filterset_class=CustomerFilter)

    account_types = graphene.List(AccountType)

    def resolve_customer(self, instance, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            try:
                return Customer.objects.filter(pk=id, is_deleted=False).first()
            except Customer.DoesNotExist:
                return None
        return None

    def resolve_customers(self, instance, **kwargs):
        return Customer.objects.filter(
            is_deleted=False
        ).order_by(
            '-id'
        ).prefetch_related(
            'mandates'
        )

    def resolve_my_customer(self, instance, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            if not instance.context.user.is_authenticated:
                return Customer.objects.none()
            else:
                return Customer.objects.filter(
                    mandate__account_officer__user=instance.context.user,
                    is_deleted=False, pk=id).distinct().order_by('-id').first()
        return None

    def resolve_my_customers(self, instance, **kwargs):
        user = instance.context.user
        if user.is_anonymous:
            raise GraphQLError('Unauthenticated User!')

        customers = Customer.objects.filter(
            Q(
                Q(mandates__account_officer__user=user) | Q(created_by=user)
            ),
            is_deleted=False
        ).distinct().order_by(
            '-id'
        ).prefetch_related(
            'mandates'
        )

        return customers

    def resolve_account_types(self, instance, **kwargs):
        account_types = [{"id": key, "name": name.lower()}
                         for key, name in Customer.ACCOUNT_TYPES]
        return account_types
