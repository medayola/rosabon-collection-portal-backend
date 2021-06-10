import graphene
from graphql.error import GraphQLError
from graphql_relay import from_global_id

from gateways.graphql.types import PaymentGatewayType
from gateways.models import PaymentGateway


class CreateGateway(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)

    id = graphene.ID(required=False)
    success = graphene.Boolean(required=True)
    gateway = graphene.Field(PaymentGatewayType)

    @staticmethod
    def mutate(self, info, **input):
        __id__ = None
        try:
            __gateway__ = PaymentGateway()
            __gateway__.name = input.get('name', '')
            __gateway__.save()
            __id__ = __gateway__.id
        except Exception as error:
            raise GraphQLError(error)

        return CreateGateway(id=__id__, success=True, gateway=__gateway__)


class DeleteGateway(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean(required=True)

    @staticmethod
    def mutate(self, info, **input):
        _, __id__ = from_global_id(input.get('id'))
        try:
            PaymentGateway.objects.get(id=__id__).delete()
        except Exception as error:
            raise GraphQLError(error)
        return DeleteGateway(success=True)


class UpdateGateway(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String(required=True)

    success = graphene.Boolean(required=True)
    gateway = graphene.Field(PaymentGatewayType)

    @staticmethod
    def mutate(self, info, **input):
        _, __id__ = from_global_id(input.get('id'))
        try:
            __payment__ = PaymentGateway.objects.get(id=__id__)
            __payment__.name = input.get('name', __payment__.name)
            __payment__.save()
        except Exception as error:
            raise GraphQLError(error)

        return UpdateGateway(success=True, gateway=__payment__)


class Mutation(graphene.ObjectType):
    create_gateway = CreateGateway.Field()
    delete_gateway = DeleteGateway.Field()
    update_gateway = UpdateGateway.Field()
