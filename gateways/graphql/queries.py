import graphene
from graphene_django.types import ObjectType

from gateways.graphql.types import PaymentGatewayType
from gateways.models import PaymentGateway
from graphene_django.filter import DjangoFilterConnectionField


class Query(graphene.ObjectType):

    payment_gateway = graphene.relay.Node.Field(PaymentGatewayType)
    payment_gateways = DjangoFilterConnectionField(PaymentGatewayType)

    def resolve_payment_gateway(self, instance, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            try:
                return PaymentGateway.objects.filter(pk=id, is_deleted=False).first()
            except PaymentGateway.DoesNotExist:
                return None
        return None

    def resolve_payment_gateways(self, instance, **kwargs):
        return PaymentGateway.objects.filter(is_deleted=False)
