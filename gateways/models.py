from django.db import models


# Create your models here.
class PaymentGateway(models.Model):
    """
    Payment Gateway Model:
    Model to hold gateways where collections are recieved from
    such as remitta, paystack or teamapt/monnify if they come on board.
    as of this writing teamapt is yet to create the bank account api.
    Feb 28, 2020 00:55
    """

    # name of the provider eg. Paystack
    name = models.CharField(max_length=200)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        string representation of Mandate
        """
        return self.name.lower()

    class Meta:
        ordering = ('-created_at', )
