import graphene


class BankInput(graphene.InputObjectType):
    """
    InputObjectType for Bank Model
    """
    name = graphene.String()
    abbreviation = graphene.String()


class CountryInput(graphene.InputObjectType):
    """
    InputObjectType for Country Model
    """
    name = graphene.String()
    abbreviation = graphene.String()


class StateInput(graphene.InputObjectType):
    """
    InputObjectType for State Model
    """
    name = graphene.String()
    abbreviation = graphene.String()
