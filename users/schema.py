from django.contrib.auth.models import Group, Permission, User

import graphene
import graphql_jwt
from gateways.models import PaymentGateway
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from users.graphql.mutations import ForgotPassword, ResetPassword


class UserType(DjangoObjectType):
    class Meta:
        model = User
        exclude_fields = ('password', )


class GroupType(DjangoObjectType):
    class Meta:
        model = Group
        exclude_fields = ()


class PermissionType(DjangoObjectType):
    class Meta:
        model = Permission
        exclude_fields = ()


class Query(graphene.ObjectType):
    user = graphene.Field(UserType)

    groups = graphene.List(GroupType)
    group = graphene.Field(GroupType)

    my_permissions = graphene.List(PermissionType)
    permissions = graphene.List(PermissionType)
    permission = graphene.Field(PermissionType)

    me = graphene.Field(UserType)

    def resolve_my_permissions(self, info, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You are not Logged In')
        permissions = []
        perms = [i.permissions.all() for i in user.groups.all()] + \
            [user.user_permissions.all()]
        for perm in perms:
            permissions.extend(perm)
        response = Permission.objects.filter(
            pk__in=[i.id for i in permissions])
        return response

    def resolve_user(self, info, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You are not Logged In')
        try:
            return User.objects.get(id=user.id)
        except Exception:
            return user

    def resolve_me(self, info, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You are not Logged In')
        try:
            user = User.objects.get(id=user.id)
        except Exception:
            pass
        return user

    def resolve_group(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            try:
                return Group.objects.filter(pk=id).first()
            except PaymentGateway.DoesNotExist:
                return None
        return None

    def resolve_groups(self, info, **kwargs):
        return Group.objects.order_by('-id')


class Mutation(graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

    request_forgot_password = ForgotPassword.Field()
    reset_password = ResetPassword.Field()
