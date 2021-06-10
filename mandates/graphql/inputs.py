import graphene

from payment_gateway.graphql.inputs import PaymentGatewayInput


class MandateInput(graphene.InputObjectType):
    """
    InputObjectType for Mandate Model
    """

    id = graphene.ID()
    code = graphene.String()
    status = graphene.Boolean()
    tenure = graphene.Int()
    initial_repayment_date = graphene.Date()


class TrailInput(graphene.InputObjectType):
    """
    InputObjectType for Trail Model
    """

    id = graphene.ID()
    payment_gateway = graphene.Field(PaymentGatewayInput)
    mandate = graphene.Field(MandateInput)


class CustomerFeeInput(graphene.InputObjectType):
    """
    InputObjectType for CustomerFee Model
    """

    id = graphene.ID()
    mandate = graphene.Field(MandateInput)
