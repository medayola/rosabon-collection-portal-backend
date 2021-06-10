import graphene
from graphene import ObjectType
from graphql.error import GraphQLError
from graphql_relay import from_global_id

from mandates.graphql.types import MandateType
from mandates.graphql.types import RentalType
from mandates.models import Rental
from pipeline.graphql.types import FormStageType
from pipeline.graphql.types import FormTypeType
from pipeline.graphql.types import ReviewCommentType
from pipeline.models import MandateReview


class RentalStoppageForm(ObjectType):

    def __init__(self, id):
        super().__init__(self)

        self.id = id
        self.compute()

    def compute(self):
        try:
            _, id = from_global_id(self.id)
            review = MandateReview.objects.get(id=id)
            self.mandate = review.mandate
            self.rentals_to_manual = Rental.objects.filter(
                pk__in=[
                    rental for _, rental in [
                        from_global_id(rent)
                        for rent in review.rentals_to_manual
                    ]
                    if rental is not None
                ]).order_by('collection_date')
            self.rentals = review.mandate.rentals.order_by('collection_date')
            self.comments = review.comments.order_by('id')
        except Exception as e:
            raise GraphQLError('Invalid Selection Made!', e)

        self.form_type = review.form_type
        self.form_stage = review.form_type.stages.filter(
            rank=review.current_position).first()
        self.is_active = review.is_deleted is False and review.active is True

    id = graphene.ID()
    mandate = graphene.Field(MandateType)
    rentals_to_manual = graphene.List(RentalType)
    rentals = graphene.List(RentalType)
    form_stage = graphene.Field(FormStageType)
    form_type = graphene.Field(FormTypeType)
    is_active = graphene.Boolean()
    comments = graphene.List(ReviewCommentType)


class MandateStoppageForm(ObjectType):

    def __init__(self, id):
        super().__init__(self)

        self.id = id
        self.compute()

    def compute(self):
        try:
            _, id = from_global_id(self.id)
            review = MandateReview.objects.get(id=id)
            self.mandate = review.mandate
            self.rentals = review.mandate.rentals.order_by('collection_date')
            self.comments = review.comments.order_by('id')
        except Exception as e:
            raise GraphQLError('Invalid Selection Made!', e)

        self.form_type = review.form_type
        self.form_stage = review.form_type.stages.filter(
            rank=review.current_position).first()
        self.is_active = review.is_deleted is False and review.active is True

    id = graphene.ID()
    mandate = graphene.Field(MandateType)
    rentals = graphene.List(RentalType)
    form_stage = graphene.Field(FormStageType)
    form_type = graphene.Field(FormTypeType)
    is_active = graphene.Boolean()
    comments = graphene.List(ReviewCommentType)
