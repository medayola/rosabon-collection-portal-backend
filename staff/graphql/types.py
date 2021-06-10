import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from mandates.graphql.types import MandateType
from staff.models import Staff, StaffCategory
from users.schema import PermissionType


class StaffCategoryType(DjangoObjectType):
    """
    DjangoObjectModel representation of the model StaffCategory
    """

    formatted_date = graphene.String()

    class Meta:
        model = StaffCategory
        filter_fields = []
        interfaces = (graphene.relay.Node,)

    def resolve_formatted_date(self, info, **kwargs):
        return self.created_at.strftime('%b %d, %Y')


class StaffType(DjangoObjectType):
    """
    DjangoObjectModel representation of the model StaffCategory
    """
    my_permissions = graphene.List(PermissionType)

    completed_mandates = DjangoFilterConnectionField(MandateType)
    pending_mandates = DjangoFilterConnectionField(MandateType)

    completed_mandates_count = graphene.Int()
    pending_mandates_count = graphene.Int()

    name = graphene.String()
    email = graphene.String()

    class Meta:
        model = Staff
        filter_fields = []
        interfaces = (graphene.relay.Node,)

    def resolve_my_permissions(self, info):
        response = self.my_permissions()
        return response

    def resolve_email(self, info):
        return self.user.email

    def resolve_name(self, info):
        return self.name()

    def resolve_completed_mandates(self, info):
        return self.mandates.filter(
            status=False
        )

    def resolve_pending_mandates(self, info):
        return self.mandates.filter(
            status=True
        )

    def resolve_completed_mandates_count(self, info):
        return self.mandates.filter(
            status=False
        ).count()

    def resolve_pending_mandates_count(self, info):
        return self.mandates.filter(
            status=True
        ).count()
