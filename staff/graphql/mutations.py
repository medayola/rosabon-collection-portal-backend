# StaffCategory Mutations
import graphene
from corsheaders import defaults
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db.transaction import atomic
from graphene_django.filter.fields import DjangoFilterConnectionField
from graphql.error import GraphQLError
from graphql_relay import from_global_id

from common.models import Department
from staff.graphql.types import StaffCategoryType, StaffType
from staff.models import Staff, StaffCategory
from users.models import Person


# create
class CreateStaffCategory(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)

    id = graphene.ID(required=True)
    success = graphene.Boolean(required=True)

    @staticmethod
    def mutate(root, instance, **input):
        _staff_category = StaffCategory()
        _staff_category.name = input.get('name')
        _staff_category.save()

        return CreateStaffCategory(success=True, id=_staff_category.id)


#  update
class UpdateStaffCategory(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String(required=True)

    success = graphene.Boolean(required=True)
    category = graphene.Field(StaffCategoryType)

    @staticmethod
    def mutate(self, instance, **input):
        try:
            _, id = from_global_id(input.get('id'))
            _staff_category = StaffCategory.objects.get(id=id)
            _staff_category.name = input.get('name')
            _staff_category.save()
            return UpdateStaffCategory(success=True, category=_staff_category)
        except Exception as e:
            return UpdateStaffCategory(success=False, category=None)


# Staff Mutations
# create
class CreateStaff(graphene.Mutation):
    class Arguments:

        username = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        gender = graphene.String(required=True)
        category = graphene.ID(required=True)
        department = graphene.ID(required=True)

    staff = graphene.Field(StaffType)
    success = graphene.Boolean(required=True)

    @staticmethod
    def mutate(root, instance, **input):
        # create a user then the staff details
        try:
            category = input.get('category')
            _, category = from_global_id(category)
            category = StaffCategory.objects.get(id=category)
        except Exception as e:
            print(f'category error: {e}')
            category = None

        try:
            department = input.get('department')
            _, department = from_global_id(department)
            department = Department.objects.get(id=department)
        except Exception as e:
            department = None

        try:
            with atomic():
                _user = get_user_model().objects.create(
                    username=input.get('username'),
                    first_name=input.get('first_name'),
                    last_name=input.get('last_name'),
                    email=input.get('email'),
                    is_staff=False,
                    password=input.get('password')
                )

                _staff = Staff.objects.create(
                    user=_user,
                    gender=input.get('gender', Person.MALE),
                    category=category,
                    department=department
                )
                return CreateStaff(success=True, staff=_staff)
        except Exception as e:
            return CreateStaff(success=False, staff=None)


class GetAccountOfficer(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)

    id = graphene.ID()
    name = graphene.String()
    success = graphene.Boolean(required=True)

    @staticmethod
    def mutate(root, info, **input):
        __name__ = ''
        __id__ = None

        try:
            __staff__ = Staff.objects.get(user__email=input.get('email', ''))
            return GetAccountOfficer(
                success=True,
                id=__staff__.user.id,
                name=__staff__.name())
        except Exception as error:
            raise GraphQLError(
                'No staff exists with email: {}'.format(input.get('email', '')))


# update
class UpdateStaff(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        username = graphene.String()
        first_name = graphene.String()
        last_name = graphene.String()
        email = graphene.String()
        password = graphene.String()
        gender = graphene.String()
        category = graphene.ID()
        department = graphene.ID()

    success = graphene.Boolean(required=True)
    staff = graphene.Field(StaffType)

    @staticmethod
    def mutate(root, instance, **input):
        # create a user then the staff details
        try:
            id = input.get('id')
            _, id = from_global_id(id)
            _staff = Staff.objects.get(id=id)
        except:
            raise GraphQLError('invalid id selected!')

        with atomic():
            # staff data
            _staff.gender = input.get('gender', _staff.gender)
            _staff.category_id = input.get('category', _staff.category.id)
            _staff.department_id = input.get(
                'department', _staff.department.id)

            # user data
            _user = _staff.user
            _user.username = input.get('username', _user.username)
            _user.first_name = input.get('first_name', _user.first_name)
            _user.last_name = input.get('last_name', _user.last_name)
            _user.email = input.get('email', _user.email)
            _user.is_staff = False

            password = input.get('password', None)
            # update password
            if password is not None and password != '':
                _user.set_password(password)

            # update user
            _user.save()

            # update staff
            _staff.save()
            return UpdateStaff(success=True, staff=_staff)
        return UpdateStaff(success=False, staff=None)


class Mutation(graphene.ObjectType):
    create_staff_category = CreateStaffCategory.Field()
    update_staff_category = UpdateStaffCategory.Field()
    create_staff = CreateStaff.Field()
    update_staff = UpdateStaff.Field()

    get_account_officer = GetAccountOfficer.Field()
