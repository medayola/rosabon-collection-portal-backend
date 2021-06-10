from mandates.models import Rental
from mandates.models import Mandate


class PaystackDeductor:

    def __init__(self):
        self.active_mandates = []
        self.active_rentals = []

    def set_active_mandates(self):
        self.active_mandates = Mandate.objects.filter(
            payment_option=Mandate.PAYSTACK,
            rentals__collection_status=Rental.ACTIVE,
            status=Mandate.ACTIVE
        ).distinct()

    def set_active_rentals(self):
        self.active_rentals = Rental.objects.filter(
            mandate__payment_option=Mandate.PAYSTACK,
            collection_status=Rental.ACTIVE,
            mandate__status=Mandate.ACTIVE
        ).distinct()

    def display(self):
        print(self.active_mandates.count())
        print(self.active_rentals.count())
