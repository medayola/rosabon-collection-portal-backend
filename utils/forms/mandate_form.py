import graphene
from graphene import ObjectType
from graphene_django.filter.fields import DjangoFilterConnectionField
from graphql_relay import from_global_id

from common.graphql.types import ProductType
from common.models import Product
from mandates.graphql.types import MandateType
from pipeline.graphql.types import FormStageType
from pipeline.graphql.types import FormTypeType
from pipeline.graphql.types import PaymentDetailType
from pipeline.models import FormType
from pipeline.models import MandateReview


class MandateForm(ObjectType):

    def __init__(self, id):
        super().__init__(self)
        self.id = id
        self.is_create = id is None or id == ''
        self.resolve_object()

    def resolve_object(self):
        try:
            _, self.pk = from_global_id(self.id)
            review = MandateReview.objects.get(id=self.pk)
        except Exception:
            review = MandateReview()
            review.form_type = FormType.objects.get(name=FormType.MANDATE)
            self.pk = review.id

        current_position = review.current_position

        self.form_type = review.form_type
        self.mandate = review.mandate
        self.form_stage = review.form_type.stages.filter(
            rank=current_position).first()
        self.current_payment_detail = review.payment_details.last()
        self.is_active = review.is_deleted is False and review.active is True

    def resolve_product(self):
        return Product.objects.exclude(is_deleted=True).order_by('name')

    id = graphene.ID()
    pk = graphene.String()

    is_active = graphene.Boolean()
    is_create = graphene.Boolean()
    form_stage = graphene.Field(FormStageType)
    form_type = graphene.Field(FormTypeType)
    mandate = graphene.Field(MandateType)
    current_payment_detail = graphene.Field(PaymentDetailType)
    products = DjangoFilterConnectionField(ProductType)
