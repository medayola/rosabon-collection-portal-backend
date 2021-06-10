import graphene
from django.conf import settings
from django.db import transaction
from graphql.error import GraphQLError

from staff.models import PasswordReset, Staff
from utils.email import Notification

# reset password


class ResetPassword(graphene.Mutation):
    class Arguments:
        token = graphene.String(required=True)
        new_password = graphene.String(required=True)

    ok = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    def mutate(root, info, **input):
        password = input.get('new_password', '')

        try:
            token = PasswordReset.objects.get(
                token__iexact=input.get('token', ''))
        except Exception:
            raise GraphQLError('invalid token entered')

        # check if token is set
        if token.is_set is False:
            raise GraphQLError('Token Expired!')

        # reset password
        with transaction.atomic():
            user = token.user
            old_password = user.password
            user.set_password(password)
            new_password = user.password
            if old_password == new_password:
                raise GraphQLError(
                    'you cannot use the same values for old and new password!')

            user.save()
            token.is_set = False
            token.save()
            return ResetPassword(
                ok=True,
                message='password successfully updated!')

        raise GraphQLError('An erorr occured while updating password!')


class ForgotPassword(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)

    ok = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    def mutate(root, info, **input):
        email = input.get('email')
        # send an email to the customer with the reset link
        try:
            staff = Staff.objects.get(user__email__iexact=email)
        except Exception:
            raise GraphQLError('Unrecognized user email!')

        try:
            reset_link = '{}/{}/{}'.format(
                settings.FRONT_END,
                'reset-password',
                staff.create_password_reset()
            )

            Notification.reset_password_requested(
                to=[staff.user.email, ],
                staff=staff,
                reset_link=reset_link)

            return ForgotPassword(
                ok=True,
                message=f"Password reset url successfully sent to: {email}"
            )
        except Exception as identifier:
            return ForgotPassword(
                ok=False,
                message=f"{identifier}")
