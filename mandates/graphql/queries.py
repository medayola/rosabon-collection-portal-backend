import graphene
from graphene_django.filter import DjangoFilterConnectionField

from mandates.graphql.filters import MandateFilter
from mandates.graphql.types import CustomerFeeType
from mandates.graphql.types import DashboadType
from mandates.graphql.types import MandateType
from mandates.graphql.types import RentalType
from mandates.graphql.types import TrialType
from mandates.models import CustomerFee
from mandates.models import Mandate
from mandates.models import Rental
from mandates.models import Trial
from utils.dashboard import Dashboard
from utils.forms.mandate_form import MandateForm
from utils.forms.rental_stoppage_form import RentalStoppageForm


class Query(graphene.ObjectType):

    mandate = graphene.relay.Node.Field(MandateType)
    mandates = DjangoFilterConnectionField(
        MandateType,
        filterset_class=MandateFilter)
    my_customer_mandate = graphene.relay.Node.Field(MandateType)
    my_customer_mandates = DjangoFilterConnectionField(
        MandateType,
        filterset_class=MandateFilter)

    rental = graphene.relay.Node.Field(RentalType)
    rentals = DjangoFilterConnectionField(RentalType)

    trial = graphene.relay.Node.Field(TrialType)
    trials = DjangoFilterConnectionField(TrialType)

    customer_fee = graphene.relay.Node.Field(CustomerFeeType)
    customer_fees = DjangoFilterConnectionField(CustomerFeeType)

    dashboard = graphene.Field(DashboadType)
    mandate_form = graphene.Field(MandateForm, id=graphene.ID(required=False))

    stop_rentals_form = graphene.Field(
        RentalStoppageForm, id=graphene.ID(required=True))

    def resolve_stop_rentals_form(self, instance, id):
        form = RentalStoppageForm(id)
        return form

    def resolve_mandate_form(self, instance, id):
        form = MandateForm(id)
        return form

    def resolve_dashboard(self, instance, **kwargs):
        dash = Dashboard()
        response = {
            'date': dash.date,
            'collections': dash.collections(),
            'monthly_expected': dash.expected_inflow(),
            'monthly_inflow': dash.monthly_inflow(),
            'monthly_customers': dash.customers_monthly()
        }
        return response

    def resolve_mandate(self, instance, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            try:
                return Mandate.objects.filter(id=id, is_deleted=False).exclude(
                    status=Mandate.PENDING).first()
            except Exception as e:
                print(e)
                return None

    def resolve_mandates(self, instance, **kwargs):
        return Mandate.objects.filter(is_deleted=False).exclude(
            status=Mandate.PENDING).order_by('-id')

    def resolve_my_customer_mandate(self, instance, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            try:
                return Mandate.objects.filter(
                    id=id,
                    is_deleted=False,
                    account_officer__user=instance.context.user
                ).exclude(
                    status=Mandate.PENDING
                ).first()
            except Exception:
                return None

    def resolve_my_customer_mandates(self, instance, **kwargs):
        return Mandate.objects.filter(
            is_deleted=False,
            account_officer__user=instance.context.user).exclude(
                status=Mandate.PENDING
        ).order_by('-id')

    def resolve_rental(self, instance, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            try:
                return Rental.objects.filter(id=id, is_deleted=False).first()
            except Exception:
                return None

    def resolve_rentals(self, instance, **kwargs):
        return Rental.objects.filter(is_deleted=False).order_by('id')

    def resolve_trial(self, instance, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            try:
                return Trial.objects.filter(pk=id, is_deleted=False).first()
            except Trial.DoesNotExist:
                return None
        return None

    def resolve_trials(self, instance, **kwargs):
        return Trial.objects.filter(is_deleted=False).order_by('id')

    def resolve_customer_fee(self, instance, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            try:
                return CustomerFee.objects.filter(
                    pk=id,
                    is_deleted=False).first()
            except CustomerFee.DoesNotExist:
                return None
        return None

    def resolve_customer_fees(self, instance, **kwargs):
        return CustomerFee.objects.filter(
            is_deleted=False
        ).order_by('-id')
