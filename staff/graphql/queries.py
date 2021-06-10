import graphene
from graphene.types import ObjectType
from graphene_django.filter import DjangoFilterConnectionField

from staff.graphql.types import StaffCategoryType, StaffType
from staff.models import Staff, StaffCategory

from staff.graphql.filters import AccountOfficerFilter


class Query(ObjectType):
    """
    Staff app queries
    """

    staff_category = graphene.relay.Node.Field(StaffCategoryType)
    staff = graphene.relay.Node.Field(StaffType)

    staff_categories = DjangoFilterConnectionField(StaffCategoryType)
    all_staff = DjangoFilterConnectionField(StaffType)
    account_officers = DjangoFilterConnectionField(
        StaffType, filterset_class=AccountOfficerFilter)

    def resolve_staff_category(self, info, **kwargs):
        id = kwargs.get('id', None)

        if id is not None:
            try:
                return StaffCategory.objects.filter(
                    id=id, is_deleted=False
                ).first()
            except Exception:
                return None
        else:
            return None

    def resolve_staff(self, info, **kwargs):
        id = kwargs.get('id', None)

        if id is not None:
            try:
                return Staff.objects.filter(
                    id=id, is_deleted=False
                ).first()
            except Exception:
                return None
        else:
            return None

    def resolve_staff_categories(self, info, **kwargs):
        return StaffCategory.objects.filter(is_deleted=False)

    def resolve_all_staff(self, info, **kwargs):
        return Staff.objects.filter(
            user__is_staff=False,
            is_deleted=False
        ).distinct()

    def resolve_account_officers(self, info, **kwargs):
        return Staff.objects.filter(
            is_account_officer=True,
            user__is_staff=False,
            is_deleted=False
        ).distinct()
