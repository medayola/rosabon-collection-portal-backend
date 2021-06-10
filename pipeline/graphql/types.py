import graphene
from graphene_django.types import DjangoObjectType

from pipeline.models import FormStage
from pipeline.models import PaymentDetail
from pipeline.models import MandateReview
from pipeline.models import FormType
from pipeline.models import ReviewComment


class FormStageType(DjangoObjectType):
    class Meta:
        model = FormStage
        filter_fields = []
        interfaces = (graphene.relay.Node,)


class FormTypeType(DjangoObjectType):
    class Meta:
        model = FormType
        filter_fields = []
        interfaces = (graphene.relay.Node,)


class PaymentDetailType(DjangoObjectType):
    class Meta:
        model = PaymentDetail
        filter_fields = []
        interfaces = (graphene.relay.Node,)

    def resolve_formatted_expiry_date(self, instance, **kwargs):
        return self.expiry_date.strftime("%Y-%m")

    formatted_expiry_date = graphene.String()


class ReviewCommentType(DjangoObjectType):

    class Meta:
        model = ReviewComment
        filter_fields = []
        interfaces = (graphene.relay.Node, )

    def resolve_created_date(self, instance, **kwargs):
        return self.created_at.strftime('%d %b, %Y')

    created_date = graphene.String()


class MandateReviewType(DjangoObjectType):
    class Meta:
        model = MandateReview
        filter_fields = []
        interfaces = (graphene.relay.Node,)

    def resolve_current_stage(self, instance, **kwargs):
        response = self.form_type.stages.filter(
            rank=self.current_position).first()
        return response

    def resolve_comments(self, instance, **kwargs):
        response = self.comments.order_by('created_at')
        return response

    current_stage = graphene.Field(FormStageType)
    comments = graphene.List(ReviewCommentType)
