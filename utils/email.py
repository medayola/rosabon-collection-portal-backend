
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

""" Email handling class """
__author__ = "Hirekaan Micheal Hemen<hemen.hirekaan@concept-nova.com>"
__version__ = "1.0"


class EmailTemplates:
    """ Abstract Template class """

    CUSTOMER_CREATION_STAFF = {
        'HTML': 'customer.creation.html',
        'SUBJECT': 'WELCOME EMAIL AND ACTIVATION MESSAGE'
    }

    CUSTOMER_CREATION_CUSTOMER = {
        'HTML': 'customer.activation.mail.html',
        'SUBJECT': '-- PAYSTACK ACTIVATION --'
    }

    STAFF_CREATED = {
        'HTML': 'staff.creation.html',
        'SUBJECT': '-- ACCOUNT CREATED --'
    }

    FORGOT_PASSWORD = {
        'HTML': 'forgot.password.html',
        'SUBJECT': '-- FORGOT PASSWORD --'
    }

    MANDATE_CREATION_STAFF = {
        'HTML': 'mandate.creation.html',
        'SUBJECT': '-- MANDATE CREATED --'
    }

    RENTAL_CONVERTED = {
        'HTML': 'rental.converted.html',
        'SUBJECT': '-- RENTAL CONVERTED TO MANUAL --'
    }

    PAYSTACK_INIT_STAFF = {
        'HTML': 'paystack.init.payment.html',
        'SUBJECT': '-- PAYSTACK ACTIVATED --'
    }

    PAYSTACK_SUCCESS = {
        'HTML': 'paystack.success.monthly.html',
        'SUBJECT': '-- PAYSTACK SUCCESS NOTICE! --'
    }

    PAYSTACK_FAILURE = {
        'HTML': 'paystack.failure.monthly.html',
        'SUBJECT': '-- PAYSTACK FAILURE NOTICE! --'
    }


class Email:
    """ Send and recieve emails """

    @staticmethod
    def send_email(
            to,
            subject,
            template_name,
            context,
            cc=None):

        sender = '\"{}\"<{}>'.format(
            settings.DEFAULT_FROM_NAME,
            settings.DEFAULT_FROM_EMAIL
        )

        if settings.DEBUG is False:
            subject = '{}'.format(subject)
        else:
            subject = '{} ({})'.format(subject, 'STAGING')

        msg_html = render_to_string(template_name, context)
        if cc is None:
            msg = EmailMessage(
                subject=subject,
                to=to,
                from_email=sender,
                body=msg_html
            )
        else:
            msg = EmailMessage(
                subject=subject,
                to=to,
                cc=cc,
                from_email=sender,
                body=msg_html
            )
        msg.content_subtype = "html"

        if settings.LOCALHOST is False:
            return msg.send()
        return True


class Notification:
    """ send notifications via email on the system """

    @staticmethod
    def customer_was_created(to, customer, staff):
        staff_context = {'customer': customer, 'staff': staff}
        customer_context = {'customer': customer}

        try:
            staff_sent = Email.send_email(
                to=to,
                subject=EmailTemplates.CUSTOMER_CREATION_STAFF['SUBJECT'],
                template_name=EmailTemplates.CUSTOMER_CREATION_STAFF['HTML'],
                context=staff_context
            )
        except Exception as e:
            print(f'[customer_was_created]: {e}')
            return False

        return True

    @staticmethod
    def reset_password_requested(to, staff, reset_link):
        context = {'staff': staff, 'reset_link': reset_link}
        try:
            return Email.send_email(
                to=to,
                subject=EmailTemplates.FORGOT_PASSWORD['SUBJECT'],
                template_name=EmailTemplates.FORGOT_PASSWORD['HTML'],
                context=context
            )
        except Exception:
            return False

    @staticmethod
    def mandate_created(to, mandate):
        amount = '{:,}'.format(round(mandate.amount, 2))

        context = {
            'officer_name': mandate.account_officer.name,
            'officer_email': mandate.account_officer.email,
            'customer_name': mandate.customer.name(),
            'customer_email': mandate.customer.email(),
            'amount': amount,
            'tenure': mandate.tenure,
            'initial_repayment_date': mandate.initial_repayment_date}

        try:
            return Email.send_email(
                to=to,
                subject=EmailTemplates.MANDATE_CREATION_STAFF['SUBJECT'],
                template_name=EmailTemplates.MANDATE_CREATION_STAFF['HTML'],
                context=context
            )
        except Exception as e:
            return False

    @staticmethod
    def mandate_created_customer(customer, url):

        context = {
            'name': customer.name().upper(),
            'url': url}

        #  amount = '{:,}'.format(round(mandate.amount, 2))
        # try:
        #     bank_name = mandate.customer.bank_detail.bank.name
        #     account_number = mandate.customer.bank_detail.account_number
        # except:
        #     bank_name = '-- NILL --'
        #     account_number = '-- NILL --'

        # context = {
        #     'staff-name': mandate.created_by.name(),
        #     'officer-name': mandate.account_officer.name,
        #     'officer-email': mandate.account_officer.email,
        #     'customer-name': mandate.customer.name(),
        #     'customer-email': mandate.customer.email(),
        #     'customer-gender': mandate.customer.gender,
        #     'customer-tel': mandate.customer.tel,
        #     'customer-bank-name': bank_name,
        #     'amount': amount,
        #     'tenure': mandate.tenure,
        #     'initial_repayment_date': mandate.initial_repayment_date,
        #     'customer-account-number': account_number}

        try:
            return Email.send_email(
                to=[customer.user.email, ],
                subject=EmailTemplates.CUSTOMER_CREATION_CUSTOMER['SUBJECT'],
                template_name=EmailTemplates.CUSTOMER_CREATION_CUSTOMER['HTML'],
                context=context
            )
        except Exception as e:
            return False

    @staticmethod
    def rental_converted(to, rental, staff):
        context = {
            'rental': rental,
            'staff': staff
        }
        try:
            return Email.send_email(
                to=to,
                subject=EmailTemplates.RENTAL_CONVERTED['SUBJECT'],
                template_name=EmailTemplates.RENTAL_CONVERTED['HTML'],
                context=context
            )
        except Exception as e:
            return False

    @staticmethod
    def staff_added_to_system(to, staff, reset_link):
        context = {'staff': staff, 'reset_link': reset_link,
                   'is_staging': settings.DEBUG}
        try:
            return Email.send_email(
                to=to,
                subject=EmailTemplates.STAFF_CREATED['SUBJECT'],
                template_name=EmailTemplates.STAFF_CREATED['HTML'],
                context=context
            )
        except Exception as e:
            return False

    @staticmethod
    def customer_accepted_paystack_charge(to, mandate):
        context = {'mandate': mandate}
        try:
            return Email.send_email(
                to=to,
                subject=EmailTemplates.PAYSTACK_INIT_STAFF['SUBJECT'],
                template_name=EmailTemplates.PAYSTACK_INIT_STAFF['HTML'],
                context=context
            )
        except Exception as e:
            return False

    @staticmethod
    def paystack_got_funds(to, mandate):
        context = {'mandate': mandate}
        try:
            return Email.send_email(
                to=to,
                subject=EmailTemplates.PAYSTACK_SUCCESS['SUBJECT'],
                template_name=EmailTemplates.PAYSTACK_SUCCESS['HTML'],
                context=context
            )
        except Exception as e:
            return False

    @staticmethod
    def paystack_missed_funds(to, mandate):
        context = {'mandate': mandate}

        try:
            return Email.send_email(
                to=to,
                subject=EmailTemplates.PAYSTACK_FAILURE['SUBJECT'],
                template_name=EmailTemplates.PAYSTACK_FAILURE['HTML'],
                context=context
            )

        except Exception as e:
            print(f'[paystack_missed_funds]: {e}')
            return False
