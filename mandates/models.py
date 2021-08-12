import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils import timezone
from django.db import models

from customers.models import Customer
from common.models import Product
from payment.transaction import PaystackTransaction
from staff.models import Staff


# Create your models here.


def __save_paystack_trial__(__rental__, __response__, __authoriation__=None):
    if __authoriation__:

        # split the authoriation response
        __status__, __is_valid__, __message__, _ = __response__

        # if the trail was a success or not create a trial and set the data
        __trial__ = Trial()
        __trial__.rental = __rental__
        __trial__.status = __is_valid__
        __trial__.message = __message__
        __trial__.save()

        __rental__.collection_status = Rental.ACTIVE

        # if the trial was a success fetch the funds
        if __is_valid__ is True and __status__ == 200:
            __transaction__ = PaystackTransaction(
                authorization_key=settings.PAYSTACK_AUTHORIZATION_KEY
            )
            status, validity, message, __charge__ = __transaction__.charge(
                email=__rental__.mandate.customer.user.email,
                auth_code=__rental__.mandate.authorization_code,
                amount=(__rental__.mandate.amount * 100),
            )

            # save the trial result
            __trial__ = Trial()
            __trial__.rental = __rental__
            __trial__.status = validity
            __trial__.message = message
            __trial__.save()

            if validity is True:
                # set the rental as completed
                __rental__.collection_status = Rental.SUCCESS
        __rental__.save()


class Mandate(models.Model):
    """
    Mandate model aka Loan Model
    As the name implies class to hold each loan taken by a customer
    """

    class Meta:
        ordering = ("-created_at",)

    def name(self):
        return "Mandate for {} for {:,}".format(
            self.customer.fullname(), round(self.amount, 2)
        )

    def __str__(self):
        """
        string representation of Mandate
        """
        return self.name()

    def total_collected(self):
        collected = sum([
            rental.collected_amount
            for rental in self.rentals.order_by('collection_date')
        ])

        return round(collected, 2)

    def current_rental(self):
        __today__ = datetime.date.today()

        # search the rentals for a rental with the same date as today
        __current_rental__ = self.rentals.filter(
            collection_date=__today__).first()

        return __current_rental__

    def trials(self):
        return Trial.objects.filter(
            rental__mandate=self
        ).order_by("-created_at")

    def next_rental_date(self):
        # self.rentals.filter(

        # )
        pass

    @property
    def has_expired(self):
        """
            method to confirm maturity of a mandate:
                - is active.
                - has all rentals as:
                    - success or
                    - manual_success
                - last due date has passed
        """

        if self.status is False:
            return False

        rentals = self.rentals.order_by('-collection_date')
        for rental in rentals:
            if rental.collection_status not in [
                Rental.SUCCESS, Rental.MANUAL_SUCCESS
            ]:
                return False

        if rental.first().collection_date <= datetime.datetime.today():
            return True

        return False

    @property
    def get_outstanding(self):
        """
            method to get the total outstanding balance for the mandate
        """

        return self.rentals.filter(collection_status=Rental.PENDING).count()

    @property
    def get_pending(self):
        """
            method to get the pending balance for the mandate
        """

        return self.rentals.filter(collection_status=Rental.PENDING, collection_date__lt=datetime.date.today()).count()

    @property
    def get_start_date(self):
        """
            method to get the mandates start date
        """

        return self.rentals.last().collection_date

    @property
    def get_end_date(self):
        """
            method to get the mandates end date
        """

        return self.rentals.first().collection_date

    @property
    def get_due_date(self):
        """
            method to get the mandates due date
        """

        return self.rentals.last().collection_date + relativedelta(months=1)





    PAYSTACK = "PAYSTACK"
    REMITTA = "REMITTA"
    PAYMENT_GATEWAYS = [
        (PAYSTACK, "PAYSTACK"),
        (REMITTA, "REMITTA"),
    ]

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    DECLINED = "DECLINED"
    DEACTIVATED = "DEACTIVATED"
    MATURED = "MATURED"
    OUTSTANDING = "OUTSTANDING"
    STATUS = [
        (PENDING, "PENDING CUSTOMER APPROVAL"),
        (DECLINED, "DECLINED"),
        (ACTIVE, "ACTIVE"),
        (DEACTIVATED, "DEACTIVATED"),
        (MATURED, "MATURED"),
        (OUTSTANDING, "OUTSTANDING"),
    ]

    customer = models.ForeignKey(
        to=Customer, on_delete=models.CASCADE, related_name="mandates"
    )
    """ The customer that took the loan """

    account_officer = models.ForeignKey(
        to=Staff, on_delete=models.CASCADE, related_name="mandates"
    )
    """ the account officer attached to the loan """

    code = models.CharField(max_length=100, blank=True, null=True)
    """ code such as mandate id code for remita """

    code_url = models.CharField(max_length=200, blank=True, null=True)
    """ access code such as extra code field """

    authorization_code = models.CharField(
        max_length=200, blank=True, null=True)
    """ authorization code for paystack and rrr for remitta """

    status = models.CharField(max_length=100, choices=STATUS, default=PENDING)
    """ status to show if the mandate is active default value is true """

    tenure = models.IntegerField(blank=False, null=False)
    """ amount of days that the loan can be taken for """

    initial_repayment_date = models.DateField(blank=False, null=False)
    """ the first repayment date """

    activated_date = models.DateField(blank=True, null=True)
    """ the date the mandate was activated """
    deactivated_date = models.DateField(blank=True, null=True)
    """ the date the mandate was deactivated """

    product = models.ForeignKey(
        to=Product,
        related_name="mandate",
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    """ product being requested """

    created_by = models.ForeignKey(
        to=Staff,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="mandates_created_by",
    )
    """ the staff who created the mandate """

    payment_option = models.CharField(
        choices=PAYMENT_GATEWAYS, default=PAYSTACK, max_length=20
    )
    """ payment method """

    amount = models.FloatField()
    """ amount to be taken every time we hit the customer's account """

    is_new = models.BooleanField(default=False)
    """ if the mandate is new """

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Rental(models.Model):
    """
    Rental Model:
    Model to show rentals on a mandate/loan
    """

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUCCESS = "SUCCESS"
    MANUAL_SUCCESS = "MANUAL SUCCESS"
    FAILED = "FAILED"
    STOPPED = "STOPPED"
    OUTSTANDING = "OUTSTANDING"

    STATUS = [
        (PENDING, "PENDING"),
        (ACTIVE, "ACTIVE"),
        (SUCCESS, "SUCCESS"),
        (MANUAL_SUCCESS, "MANUAL_SUCCESS"),
        (FAILED, "FAILED"),
        (STOPPED, "STOPPED"),
        (OUTSTANDING, "OUTSTANDING"),

    ]

    mandate = models.ForeignKey(
        Mandate, on_delete=models.CASCADE, related_name="rentals"
    )
    collection_date = models.DateField()
    collected_date = models.DateField(blank=True, null=True)
    collection_status = models.CharField(
        max_length=100, choices=STATUS, default=PENDING
    )

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} [ {} ] - {}".format(
            self.mandate.name(), self.collection_date, self.collection_status
        )

    class Meta:
        ordering = ("-collection_date",)

    def get_funds(self):
        if self.mandate.payment_option == Mandate.PAYSTACK:
            # get the paystack collection to run
            __pystack__ = PaystackTransaction(
                authorization_key=settings.PAYSTACK_AUTHORIZATION_KEY
            )

            # get the customer's authorization code
            __authoriation__ = self.mandate.authorization_code

            if __authoriation__ is not None:
                # check for availabilty of funds
                try:
                    __response__ = __pystack__.check(
                        # convert amount to kobo
                        amount=(self.mandate.amount * 100),
                        email=self.mandate.customer.user.email,
                        authorization_code=__authoriation__,
                    )
                except Exception:
                    __response__ = None

                __save_paystack_trial__(self, __response__, __authoriation__)

    @property
    def collected_amount(self):

        data = 0.00
        try:
            if self.collection_status == Rental.MANUAL_SUCCESS:
                data = self.mandate.amount
            else:
                data = sum([
                    i.collected_amount for i in self.trials.filter(
                        status=True
                    ) if i.collected_amount is not None
                ])
        except Exception:
            pass

        return round(data, 2) if data > 0 else 0.0

    @property
    def pending_amount(self):
        try:
            if self.collection_status == Rental.MANUAL_SUCCESS:
                sum_value = self.mandate.amount
            else:
                sum_value = sum([
                    i.collected_amount
                    for i in self.trials.filter(
                        status=True
                    ) if i.collected_amount is not None
                ])
        except Exception:
            sum_value = 0.00

        return self.mandate.amount - round((
            sum_value if sum_value > 0 else 0
        ), 2)


class Trial(models.Model):
    """
    Trial Model:
    Model to show results from requests from gateways of recieving collections
    """

    rental = models.ForeignKey(
        to=Rental, on_delete=models.CASCADE, related_name="trials"
    )

    # the status of the trial
    status = models.BooleanField(default=False)
    collected_amount = models.FloatField(default=0.0)

    # message from trial
    message = models.CharField(max_length=250, blank=True, null=True)
    reference_code = models.IntegerField(blank=True, null=True)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        string representation of Trial
        """
        status = "Failed"
        if self.status:
            status = "Succeeded"
        return "{} | status: {}".format(self.rental.mandate, status)

    class Meta:
        ordering = ("-created_at",)


class CustomerFee(models.Model):
    """
    CustomerFee Model:
    Model to show fees accured by customer
    """

    mandate = models.ForeignKey(
        to=Mandate, related_name="fees", on_delete=models.CASCADE
    )

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        string representation of CustomerFee
        """
        return ""

    class Meta:
        ordering = ("-created_at",)


class Billing(models.Model):
    """
    Billing Model:
    Model to billing details of a mandate accured by customer
    """

    class Meta:
        ordering = ('id',)

    mandate = models.ForeignKey(
        to=Mandate, related_name="billing_details", on_delete=models.CASCADE
    )

    billing_name = models.CharField(
        max_length=100, default='', blank=True, null=True)
    billing_card_expiry_date = models.DateField()
    billing_card_type = models.CharField(max_length=100)
    billing_bank = models.CharField(max_length=100)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        string representation of Billing
        """
        return ""
