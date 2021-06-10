from graphene_django.types import DjangoObjectType
import graphene
from gateways.models import PaymentGateway


class PaymentGatewayType(DjangoObjectType):
    """
    DjangoObjectType for Payment Gateway Model
    """

    class Meta:
        model = PaymentGateway
        filter_fields = []
        interfaces = (graphene.relay.Node,)
