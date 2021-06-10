import graphene
from graphene import ObjectType
from graphene_django.filter.fields import DjangoFilterConnectionField

from pipeline.models import PaymentDetail

from pipeline.graphql.types import FormStageType
from pipeline.graphql.types import FormTypeType
from pipeline.graphql.types import MandateReviewType
from pipeline.graphql.types import PaymentDetailType
from pipeline.models import FormStage
from pipeline.models import FormType
from pipeline.models import MandateReview
from pipeline.graphql.filters import MandateReviewFilter
from utils.forms.rental_stoppage_form import MandateStoppageForm


class Query(ObjectType):
    form_stages = DjangoFilterConnectionField(FormStageType)
    form_stage = graphene.relay.Node.Field(FormStageType)

    form_types = DjangoFilterConnectionField(FormTypeType)
    form_type = graphene.relay.Node.Field(FormTypeType)

    mandate_reviews = DjangoFilterConnectionField(
        MandateReviewType, filterset_class=MandateReviewFilter)
    mandate_review = graphene.relay.Node.Field(MandateReviewType)

    deactivation_mandate_review = graphene.Field(
        MandateStoppageForm, id=graphene.ID(required=True))
    deactivation_mandate_reviews = DjangoFilterConnectionField(
        MandateReviewType, filterset_class=MandateReviewFilter)

    payment_details = DjangoFilterConnectionField(PaymentDetailType)
    payment_detail = graphene.relay.Node.Field(PaymentDetailType)

    def resolve_payment_details(self, instance, **kwargs):
        return PaymentDetail.objects.exclude(is_deleted=True)

    def resolve_payment_detail(self, instance, **kwargs):
        response = PaymentDetail.objects.exclude(
            is_deleted=True).filter(pk=kwargs.get('id')).first()
        return response

    def resolve_form_stages(self, instance, **kwargs):
        return FormStage.objects.exclude(is_deleted=True)

    def resolve_form_stage(self, instance, **kwargs):
        response = FormStage.objects.exclude(
            is_deleted=True).filter(pk=kwargs.get('id')).first()
        return response

    def resolve_form_types(self, instance, **kwargs):
        return FormType.objects.exclude(is_deleted=True)

    def resolve_form_type(self, instance, **kwargs):
        return FormType.objects.exclude(
            is_deleted=True
        ).filter(
            pk=kwargs.get('id')
        ).first()

    def resolve_mandate_reviews(self, instance, **kwargs):
        qs = MandateReview.objects.exclude(
            is_deleted=True
        ).filter(
            active=True
        ).exclude(
            form_type=FormType.objects.get(
                name=FormType.STOP_MANDATE
            )
        ).order_by('created_at')

        return qs

    def resolve_mandate_review(self, instance, **kwargs):
        mx = MandateReview.objects.exclude(
            is_deleted=True
        ).filter(
            pk=kwargs.get('id'), active=True
        ).exclude(
            form_type=FormType.objects.get(
                name=FormType.STOP_MANDATE
            )
        )
        return mx.first()

    def resolve_deactivation_mandate_reviews(self, instance, **kwargs):
        qs = MandateReview.objects.exclude(
            is_deleted=True
        ).filter(
            active=True
        ).filter(
            form_type=FormType.objects.get(
                name=FormType.STOP_MANDATE
            )
        ).order_by('created_at')
        return qs

    def resolve_deactivation_mandate_review(self, instance, **input):
        form = MandateStoppageForm(input.get('id'))
        return form
