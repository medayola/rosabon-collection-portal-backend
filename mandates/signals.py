from django.conf import settings
from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver
from pypaystack import Customer as PaystackCustomer
from mandates.models import Mandate, Trial, Rental
from payment.transaction import PaystackTransaction
from utils.email import Notification

#####################################################
#####################################################
#
# SIGNALS
#
#####################################################
#####################################################


@receiver(pre_save, sender=Mandate)
def __before_saving_mandate__(sender, instance, **kwargs):
    # get all active mandates belonging to the said customer
    customer = instance.customer
    if instance._state.adding:
        if customer.mandates.filter(status=Mandate.ACTIVE).count() > 0:
            raise Exception('Customer already has active mandate')
        if customer.mandates.filter(status=Mandate.PENDING).count() > 0:
            raise Exception(
                'Customer already has mandate awaiting confirmation')


@receiver(post_save, sender=Mandate)
def __create_paystack_request__(sender, instance, created, **kwargs):
    if created:
        if instance.payment_option == Mandate.PAYSTACK:
            # create the customer
            __customer__ = PaystackCustomer(
                authorization_key=settings.PAYSTACK_AUTHORIZATION_KEY)
            (
                __code__,
                _,
                _,
                __response__,
            ) = __customer__.create(
                instance.customer.user.email,
                instance.customer.user.first_name,
                instance.customer.user.last_name)

            if __code__ == 200:
                instance.customer.identification_pin = __response__[
                    'customer_code']
                instance.customer.save()

                # create the transaction
                __transaction__ = PaystackTransaction(
                    authorization_key=settings.PAYSTACK_AUTHORIZATION_KEY)

                # generate the url to send to the customer
                __code__, _, _, __charge__ = __transaction__.initialize(
                    email=instance.customer.user.email,
                    amount=settings.PAYSTACK_INITIAL_FEE,
                    channel=['card', ],
                    callback_url=settings.PAYSTACK_CALLBACK_URL
                )

                if __code__ == 200:
                    instance.code = __charge__['reference']
                    instance.code_url = __charge__['authorization_url']

                    # send an email to the customer that the mandate
                    # was created successfully
                    # if it is a new mandate alert the user
                    if instance.is_new:
                        Notification.mandate_created_customer(
                            customer=instance.customer,
                            url=__charge__['authorization_url'])


@receiver(post_save, sender=Trial)
def send_trial_status(sender, instance, **kwargs):
    if kwargs['created']:
        try:
            # send mail to account officer
            to = [
                email for email in [
                    instance.rental.mandate.account_officer.user.email,
                ] if email != ''
            ]
            if instance.status is True:
                Notification.paystack_got_funds(
                    to=to, mandate=instance.rental.mandate)
        except Exception as e:
            print('[send_trial_status]: {}'.format(e))

    if instance.rental.pending_amount <= 0:
        instance.rental.collection_status = Rental.SUCCESS
    else:
        instance.rental.collection_status = Rental.ACTIVE
    instance.rental.save()
    """ Update the rental based on the trial """
