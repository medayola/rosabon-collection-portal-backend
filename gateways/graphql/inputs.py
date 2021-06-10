import graphene


class PaymentGatewayInput(graphene.InputObjectType):
    """
    InputObjectType for Payment Gateway
    """

    id = graphene.ID()
    name = graphene.String()
