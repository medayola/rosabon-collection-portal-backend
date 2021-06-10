import datetime
from django.db.models import Q
from calendar import monthrange

from mandates.models import Rental
from mandates.models import Mandate
from customers.models import Customer


class Dashboard:
    def __init__(self):
        self.date = datetime.date.today()
        self.first = self.date.replace(day=1)

        self.monthly_expected = 0.0
        self.expected = 0.0
        self.collected = 0.0

        self.fetch_expected_and_collected()
        """ fetch the chart data """

    def fetch_expected_and_collected(self):
        _, last_day = monthrange(
            year=self.date.year,
            month=self.date.month)

        rentals = Rental.objects.all()

        qs = rentals.filter(
            collection_status=Rental.ACTIVE,
            collection_date__lte=datetime.date(
                year=self.date.year,
                month=self.date.month,
                day=1
            )
        )
        """ rentals that are yet to be collected """

        monthly = rentals.filter(
            collection_status=Rental.ACTIVE,
            collection_date__year=self.date.year,
            collection_date__month=self.date.month
        )
        """ active rentals for the current month """

        success = rentals.filter(
            Q(collection_status=Rental.SUCCESS) | Q(
                collection_status=Rental.MANUAL_SUCCESS),
            collection_date__year=self.date.year,
            collection_date__month=self.date.month
        )
        """ recieved rentals """

        self.monthly_expected = monthly | success
        self.monthly_expected = sum(
            i.mandate.amount for i in self.monthly_expected.order_by('id'))

        self.expected = qs | monthly | success
        self.expected = sum(
            i.mandate.amount for i in self.expected.order_by('id'))

        self.collected = sum(i.mandate.amount for i in success.order_by('id'))

    def collections(self):
        try:
            return round((self.collected * 100 / self.expected), 2)
        except Exception:
            return 0.0

    def monthly_inflow(self):
        return round(self.collected, 2)

    def expected_inflow(self):
        return round(self.monthly_expected, 2)

    def total_expected_inflow(self):
        return round(self.expected, 2)

    def customers_monthly(self):
        today = datetime.date.today()
        qs = Customer.objects.filter(
            mandates__status=Mandate.ACTIVE,
            mandates__initial_repayment_date__year=today.year,
            mandates__initial_repayment_date__month=today.month
        ).distinct()
        """ get all the active mandates """

        return qs.count()
