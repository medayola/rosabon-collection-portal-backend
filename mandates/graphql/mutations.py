from datetime import datetime

import pandas as pd

import graphene
from django.conf import settings
from django.db import transaction
from graphql.error import GraphQLError
from graphql_relay import from_global_id

from dateutil import parser

from common.models import Product
from customers.models import Customer
from mandates.models import Mandate, Rental, Trial
from mandates.graphql.types import MandateType
from pipeline.graphql.types import MandateReviewType
from pipeline.models import FormType
from pipeline.models import MandateReview
from pipeline.models import ReviewComment
from staff.models import Staff
from utils.email import Notification
from utils.cron import activate_paystack_rentals
from utils.report_generator import ReportGenerator


class MandateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        current_stage = graphene.ID(required=False)
        form_type = graphene.ID(required=False)
        customer = graphene.ID(required=True)
        account_officer = graphene.ID(required=True)
        tenure = graphene.Int(required=True)
        initial_repayment_date = graphene.String(required=True)
        amount = graphene.String(required=True)
        code = graphene.String()
        product = graphene.ID(required=True)
        payment_option = graphene.String(required=True)
        rentals = graphene.List(graphene.String, required=True)
        authorization_code = graphene.String()
        is_active = graphene.Boolean(required=True)

    id = graphene.ID()
    success = graphene.Boolean(required=True)
    mandate = graphene.Field(MandateType)

    @staticmethod
    def mutate(root, info, **input):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('Unauthenticated User!')
        try:
            _, __id__ = from_global_id(input.get('id', ''))
        except Exception:
            __id__ = None

        if len(input['rentals']) <= 0:
            raise GraphQLError(
                'Kindly refresh the page as the rentals are empty!')

        __customer__ = input.get('customer')
        __account_officer__ = input.get('account_officer')
        __rentals__ = (
            datetime.strptime(
                "{}-{}-{}".format(
                    i[0],
                    int(i[1]) + 1, i[2]
                ), "%Y-%m-%d") for i in (
                    x.split('-')
                for x in input.get('rentals', [])
            )
        )

        # unhash ids
        try:
            __review__ = MandateReview.objects.get(id=__id__)
            __mandate__ = MandateReview.mandate
        except Exception:
            __review__ = MandateReview()
            __mandate__ = Mandate()

        try:
            __customer__ = Customer.objects.get(user__id=__customer__)
        except Exception:
            raise GraphQLError('Invalid Customer Selected!')

        try:
            __account_officer__ = Staff.objects.get(
                user__id=__account_officer__)
        except Exception:
            raise GraphQLError('Invalid Account Officer Selected!')

        __tenure__ = input.get('tenure', __mandate__.tenure)
        try:
            __tenure__ = int(__tenure__)
            if __tenure__ == 0:
                raise GraphQLError('Invalid Tenure entered!')
        except Exception as error:
            raise GraphQLError(error)

        __repayment_initial_date__ = input.get(
            'initial_repayment_date', None)

        if __repayment_initial_date__ is None:
            raise GraphQLError('Invalid Repayment Date!')

        try:
            __repayment_initial_date__ = datetime.strptime(
                __repayment_initial_date__, '%Y-%m-%d')
        except Exception as error:
            raise GraphQLError(error)

        # clean the amount
        __amount__ = input.get('amount', '0')
        __amount__ = ''.join(__amount__.split(','))
        try:
            __amount__ = float(__amount__)
            if __amount__ <= 0:
                raise GraphQLError(
                    'Invalid amount {} entered'.format(__amount__))
        except Exception as error:
            raise GraphQLError(error)

        try:
            _, product = from_global_id(input.get('product'))
            product = Product.objects.get(id=product)
        except Exception:
            raise GraphQLError('Invalid Product Selected!')

        with transaction.atomic():
            is_new = not input.get('is_active', True)

            __mandate__.customer = __customer__
            __mandate__.account_officer = __account_officer__
            __mandate__.code = input.get('code', '')
            __mandate__.tenure = __tenure__
            __mandate__.initial_repayment_date = __repayment_initial_date__
            __mandate__.amount = __amount__
            __mandate__.product = product
            __mandate__.created_by = Staff.objects.get(user=info.context.user)
            __mandate__.payment_option = input.get('payment_option')
            __mandate__.is_new = is_new

            __form_type__ = FormType.objects.get(
                is_deleted=False,
                name=FormType.MANDATE
            )
            __review__.form_type = __form_type__

            # if not is_new:
            #     __mandate__.status = Mandate.ACTIVE
            #     __review__.foward()

            __mandate__.authorization_code = input.get('authorization_code')
            __mandate__.payment_option = input.get('payment_option')
            __mandate__.save()

            __review__.mandate = __mandate__
            __review__.code = __mandate__.code
            __review__.code_url = __mandate__.code_url
            __review__.authorization_code = __mandate__.authorization_code

            __review__.foward()
            __review__.save()

            __loggedin_user__ = info.context.user.email
            __loggedin_users_hod__ = ''

            if info.context.user.staff:
                staff = info.context.user.staff
                if staff.department.head:
                    __loggedin_users_hod__ = staff.department.head.email

            try:
                to = [
                    email for email in [
                        __account_officer__.email(),
                        __loggedin_user__,
                        __loggedin_users_hod__
                    ] if email != '']
                Notification.mandate_created(to=to, mandate=__mandate__)
            except Exception as e:
                print('[]: {}'.format(e))

            # create rentals
            [
                Rental.objects.create(
                    mandate=__mandate__,
                    collection_date=__d__
                ) for __d__ in __rentals__
            ]

            # start all required mandates
            activate_paystack_rentals()

            return MandateMutation(
                id=__review__.id,
                success=True,
                mandate=__mandate__)
        return MandateMutation(id=None, success=False, mandate=None)


class RentalManualCollection(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)  # mandate id
        rentals = graphene.List(graphene.ID, required=True)

    response = graphene.Field(MandateReviewType, required=True)
    success = graphene.Boolean(required=True)

    @staticmethod
    def mutate(cls, info, **input):
        # get the id
        try:
            _, id = from_global_id(input.get('id'))
            mandate = Mandate.objects.get(id=id)
        except Exception:
            raise GraphQLError(f"Invalid Mandate Selected! {input.get('id')}")

        with transaction.atomic():
            # update the rental
            review = MandateReview()
            review.rentals_to_manual = input.get('rentals', [])
            review.mandate = mandate
            review.form_type = FormType.objects.get(
                is_deleted=False, name=FormType.RENTAL)
            review.save()

            return RentalManualCollection(response=review, success=True)
        return RentalManualCollection(response=None, success=False)


class ReportGenerationMutation(graphene.Mutation):
    class Arguments:
        status = graphene.String()
        type = graphene.String(required=True)
        start_date = graphene.String(required=True)
        end_date = graphene.String(required=True)

    success = graphene.Boolean(required=True)
    message = graphene.String(required=True)
    name = graphene.String(required=True)
    url = graphene.String(required=True)

    @staticmethod
    def mutate(root, info, **input):
        status = input.get('status', None)
        """ create a report using the sent status """

        start_date = input.get('start_date')
        """ the start date for range searches """

        end_date = input.get('end_date')
        """ the end date for range searches """

        generator = ReportGenerator()

        if start_date and end_date:
            try:
                generator.start_date = parser.parse(input.get('start_date'))
                generator.end_date = parser.parse(input.get('end_date'))
            except Exception:
                raise GraphQLError("Invalid dates selected!")

        generator.status = status

        if status == '' or status is None or status == '0':
            status = 'ALL'
            """ set the status to all """
            generator.status = status
            generator.resolve_all_mandates(
                start_date=parser.parse(input.get('start_date')),
                end_date=parser.parse(input.get('end_date')),
                status=status
            )

        elif status == 'INFLOW (RECIEVED)':
            """ get recieved inflow """

            generator.resolve_inflow_recieved()

        elif status == 'INFLOW (EXPECTED)':
            """ get expected inflow """

            generator.resolve_inflow_expected()

        else:
            generator.resolve_all_mandates(
                start_date=parser.parse(input.get('start_date')),
                end_date=parser.parse(input.get('end_date')),
                status=status
            )

        generator.printer.filetype = input.get('type').upper()
        generator.printer.print()

        return ReportGenerationMutation(
            success=True,
            url=generator.printer.media_url,
            name=generator.printer.filename,
            message='Report Generated Successfully!'
        )


class ReviewMandate(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        status = graphene.Boolean(required=True)
        comment = graphene.String(required=True)

    success = graphene.Boolean(required=True)

    @staticmethod
    def mutate(root, info, **input):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('Unauthenticated User!')
        try:
            _, id = from_global_id(input.get('id', ''))
            review = MandateReview.objects.get(id=id)
            mandate = review.mandate
        except Exception:
            raise GraphQLError('Invalid Mandate!')

        with transaction.atomic():
            if input.get('status', False) is True:
                mandate.status = Mandate.ACTIVE
            else:
                mandate.status = Mandate.DECLINED
            mandate.save()

            review.active = False
            review.foward()
            review.save()

            ReviewComment(
                actor=Staff.objects.get(user=user),
                comment=input.get('comment', ''),
                mandate_review=review
            ).save()

            return ReviewMandate(success=True)
        return ReviewMandate(success=False)


class ReviewRental(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        type = graphene.String(required=True)
        comment = graphene.String()

    ok = graphene.Boolean(required=True)
    success = graphene.Boolean(required=True)

    @staticmethod
    def mutate(root, info, **input):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('Unauthenticated User!')
        ok = False

        try:
            _, id = from_global_id(input.get('id'))
            review = MandateReview.objects.get(id=id)
        except Exception:
            raise GraphQLError('Invalid Selection!')

        with transaction.atomic():

            if input.get("type") == settings.SAVE_CLICKED:
                # move the form foward
                review.foward()
            elif input.get("type") == settings.CANCEL_CLICKED:
                # end/delete the form
                review.is_deleted = True
            elif input.get("type") == settings.DECLINE_CLICKED:
                # end the form and send an email
                review.foward()
                review.active = False
            elif input.get("type") == settings.APPROVE_CLICKED:
                # stop rentals
                for i in review.rentals_to_manual:
                    try:
                        _, __id__ = from_global_id(i)
                        rental = Rental.objects.get(
                            id=__id__, is_deleted=False)
                        rental.collection_status = Rental.MANUAL_SUCCESS
                        rental.save()
                        ok = True
                    except Exception:
                        pass
                # end the form
                review.foward()
                review.active = False

            review.save()
            ReviewComment(
                mandate_review=review,
                comment=input.get('comment', ''),
                actor=Staff.objects.get(user=user)
            ).save()
            return ReviewRental(success=True, ok=ok)
        return ReviewRental(success=False, ok=ok)


class MandateTransactions(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()
    message = graphene.String()
    file_url = graphene.String()
    media_url = graphene.String()

    @staticmethod
    def mutate(root, info, **input):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('Unauthenticated User!')
        ok = False

        try:
            _, id = from_global_id(input.get('id'))
            mandate = Mandate.objects.get(id=id)
        except Exception:
            raise GraphQLError('Invalid Selection!')

        qs = Trial.objects.filter(
            rental__mandate=mandate
        ).distinct()

        sheet_data = [
            {
                "Customer Email": value.rental.mandate.customer.email(),
                "Expected Rental": round(value.rental.mandate.amount, 2),
                "Status": value.status,
                "Date": value.created_at.strftime("%d/%m/%Y"),
                "Amount Taken": round(value.collected_amount, 2),
                "Gateway Response": value.message
            }
            for key, value in enumerate(qs.order_by('created_at'))
        ]

        filename = str(datetime.now().timestamp())
        filename = filename.replace('.', '')
        media_url = f"{settings.MEDIA_URL}{filename}.xlsx"
        file_url = f"{settings.MEDIA_ROOT}{filename}.xlsx"

        pd.DataFrame(sheet_data).to_excel(file_url)

        return MandateTransactions(
            ok=ok,
            file_url=file_url,
            media_url=media_url,
            message="File Successfully created!"
        )


class StopMandateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        comment = graphene.String()

    ok = graphene.Boolean(required=True)
    success = graphene.Boolean(required=True)

    @staticmethod
    def mutate(root, info, **input):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('Unauthenticated User!')
        ok = False

        try:
            _, id = from_global_id(input.get('id'))
            mandate = Mandate.objects.get(id=id)
        except Exception:
            raise GraphQLError('Invalid Selection!')

        with transaction.atomic():
            try:
                review = MandateReview(
                    mandate=mandate,
                    form_type=FormType.objects.get(name=FormType.STOP_MANDATE),
                    active=True
                )
                review.save()

                if input.get('comment', None):
                    ReviewComment(
                        mandate_review=review,
                        comment=input.get('comment'),
                        actor=Staff.objects.get(user=user)
                    ).save()

                # for rental in mandate.rentals.all():
                #     rental.collection_status = Rental.STOPPED
                #     rental.save()
                # """ stop each rental belonging to the mandate """

                # mandate.status = Mandate.DEACTIVATED
                # mandate.save()
                # """ deactivate mandate """
            except Exception as e:
                print(e)

            return ReviewRental(success=True, ok=ok)
        return ReviewRental(success=False, ok=ok)


class UpdateMandateStoppage(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        comment = graphene.String(required=True)
        form_type = graphene.String(required=True)

    ok = graphene.Boolean()

    @staticmethod
    def mutate(root, info, **input):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('Unauthenticated User!')

        try:
            _, id = from_global_id(input.get('id'))
            review = MandateReview.objects.get(id=id)
        except Exception:
            raise GraphQLError('Invalid Selection!')

        with transaction.atomic():

            if input.get("form_type") == settings.SAVE_CLICKED:
                # move the form foward
                review.foward()
                # send notification to the user and
                # suppervisors in the department
            elif input.get("form_type") == settings.CANCEL_CLICKED:
                # end/delete the form
                review.is_deleted = True
            elif input.get("form_type") == settings.DECLINE_CLICKED:
                # end the form and send an email
                review.foward()
                review.active = False
                # send notification to collections
                # officer that last pushed a comment

                # send notification to current officer
            elif input.get("form_type") == settings.APPROVE_CLICKED:
                # stop rentals
                for rental in review.mandate.rentals.all():
                    rental.collection_status = Rental.STOPPED
                    rental.save()
                # end the form
                review.foward()
                review.active = False

                mandate = review.mandate
                mandate.status = Mandate.DEACTIVATED
                mandate.deactivated_date = datetime.today()
                mandate.save()

            review.save()
            ReviewComment(
                mandate_review=review,
                comment=input.get('comment', ''),
                actor=Staff.objects.get(user=user)
            ).save()
            return UpdateMandateStoppage(ok=True)
        return UpdateMandateStoppage(ok=False)


class Mutation(graphene.ObjectType):
    mandate_mutation = MandateMutation.Field()
    generate_report = ReportGenerationMutation.Field()
    convert_to_manual = RentalManualCollection.Field()
    stop_mandate = StopMandateMutation.Field()
    update_mandate_stoppage = UpdateMandateStoppage.Field()
    download_mandate_transactions = MandateTransactions.Field()
    review_mandate = ReviewMandate.Field()
    review_rental = ReviewRental.Field()
