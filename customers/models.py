from django.contrib.auth.models import User
from django.db import models

from common.models import Bank, Branch
from users.models import Person
from utils.formatters import Formatters

# Create your models here.


class Customer(Person):

    class Meta:
        verbose_name = 'customer'
        verbose_name_plural = 'customers'

    def name(self):
        return ' '.join([self.user.first_name.lower(),
                         self.user.last_name.lower()])

    def email(self):
        return '{}'.format(self.user.email)

    def fullname(self):
        if self.account_type == self.PERSONAL_ACCOUNT:
            return '{} {}'.format(
                self.user.first_name.lower(),
                self.user.last_name.lower())
        elif self.account_type == self.COPORATE_ACCOUNT:
            return '{}'.format(self.company_name.lower())

    def __str__(self):
        """
        string representation of customer
        """
        return '{} ({} {})'.format(
            self.fullname(),
            self.account_type, "account.".upper())

    PERSONAL_ACCOUNT = 'PERSONAL'
    COPORATE_ACCOUNT = 'CORPORATE'

    ACCOUNT_TYPES = [
        (PERSONAL_ACCOUNT, PERSONAL_ACCOUNT),
        (COPORATE_ACCOUNT, COPORATE_ACCOUNT),
    ]

    account_type = models.CharField(
        choices=ACCOUNT_TYPES,
        max_length=10,
        default=PERSONAL_ACCOUNT
    )

    company_name = models.CharField(
        max_length=200, unique=True, blank=True, null=True)

    identification_pin = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default='')

    paystack_email = models.CharField(
        default='', max_length=200, blank=True, null=True)
    """ paystack email address """

    branch = models.ForeignKey(
        to=Branch,
        related_name='customers',
        on_delete=models.CASCADE,
        blank=True,
        null=False)
    """ the branch the customer was created at """

    created_by = models.ForeignKey(
        to=User, related_name='created_customers', on_delete=models.CASCADE)
    """ created by this serves as the account officer """

    underwriter = models.ForeignKey(
        to=User,
        related_name='u_created_customers',
        null=True,
        on_delete=models.CASCADE)
    """ underwriter who saved the customer """


class BankingDetail(models.Model):
    """
    Banking detail for a customer holding the customers
    bank and account number
    """

    customer = models.OneToOneField(
        to=Customer, related_name='bank_detail', on_delete=models.CASCADE)

    bank = models.ForeignKey(
        to=Bank, related_name='bank_detail', on_delete=models.CASCADE)

    account_number = models.CharField(max_length=20)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """ string representation of the Banking detail model """
        account_number = Formatters.split_account_number(self.account_number)
        return "account number '{}' with bank '{}' belongs to: {}".format(
            account_number, self.bank, self.customer)

    class Meta:
        ordering = ('-created_at', )
