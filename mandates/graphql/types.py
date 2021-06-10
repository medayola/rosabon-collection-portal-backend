import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType

from dateutil.relativedelta import relativedelta

from mandates.models import CustomerFee, Mandate, Rental, Trial


class RentalType(DjangoObjectType):
    """
    DjangoObjectType for the Rental Model
    """

    formatted_collection_date = graphene.String()
    formatted_collected_date = graphene.String()
    is_stopable = graphene.Boolean()

    class Meta:
        model = Rental
        filter_fields = []
        interfaces = (graphene.relay.Node,)

    def resolve_formatted_collection_date(self, info):
        try:
            return self.collection_date.strftime('%A, %B %d, %Y')
        except Exception:
            return None

    def resolve_formatted_collected_date(self, info):
        try:
            return self.collected_date.strftime('%A, %B %d, %Y')
        except Exception:
            return None

    def resolve_is_stopable(self, info):
        try:
            return self.collection_status != Rental.PENDING
        except Exception:
            return True


class TrialType(DjangoObjectType):
    """
    DjangoObjectType for the Trial Model
    """

    class Meta:
        model = Trial
        filter_fields = []
        interfaces = (graphene.relay.Node,)


class MandateType(DjangoObjectType):
    """
    DjangoObjectType for the Mandate Model
    """
    formatted_amount = graphene.String()
    start_date = graphene.String()
    end_date = graphene.String()
    trials = DjangoFilterConnectionField(TrialType)
    rentals = DjangoFilterConnectionField(RentalType)

    class Meta:
        model = Mandate
        filter_fields = ['customer', ]
        interfaces = (graphene.relay.Node,)

    def resolve_trials(self, info):
        return self.trials()

    def resolve_rentals(self, info):
        return self.rentals.order_by('id')

    def resolve_start_date(self, info):
        init = self.initial_repayment_date
        return init.strftime("%b %d, %Y")

    def resolve_end_date(self, info):
        init = self.initial_repayment_date
        init += relativedelta(months=self.tenure - 1)
        return init.strftime("%b %d, %Y")

    def resolve_formatted_amount(self, info):
        return '{:,}'.format(round(self.amount, 2))


class CustomerFeeType(DjangoObjectType):
    """
    DjangoObjectType for the CustomerFee Model
    """

    class Meta:
        model = CustomerFee
        filter_fields = []
        interfaces = (graphene.relay.Node,)


class DashboadType(graphene.ObjectType):
    """
    Django representation of the dashboard
    """

    date = graphene.Date()
    first = graphene.Date()
    formatted_date = graphene.String()
    collections = graphene.String()
    monthly_expected = graphene.String()
    monthly_inflow = graphene.String()
    monthly_customers = graphene.String()

    def resolve_formatted_date(self, info):
        return self['date'].strftime('%b, %Y')

    def resolve_collections(self, info):
        return '{:,}'.format(self['collections'])

    def resolve_monthly_expected(self, info):
        return '{:,}'.format(self['monthly_expected'])

    def resolve_monthly_inflow(self, info):
        return '{:,}'.format(self['monthly_inflow'])

    def resolve_monthly_customers(self, info):
        return '{:,}'.format(self['monthly_customers'])
