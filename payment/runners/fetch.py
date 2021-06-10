import datetime

from django.db.models import Q

from mandates.models import Rental
from django.conf.settings import RENTAL_WIDTH_IN_DAYS


class RentalRunner:
    """
    Class to run rental trials
    get funds from customer accounts
    """

    def __init__(self):
        self.__active_rentals__ = []
        self.__missed_rentals__ = []

    def __fetch_active_rentals__(self):
        self.__active_rentals__ = Rental.objects.filter(
            collection_date=datetime.date.today(),
            collection_status=Rental.ACTIVE,
            is_deleted=False)

    def __run_active_rentals__(self):
        # for __rental__ in self.__active_rentals__:
            # __rental__.get_funds()
        pass
 
    def __fetch_missed_rentals__(self):
        __end_date__ = datetime.date.today()
        __start_date__ = __end_date__ - \
            datetime.timedelta(days=RENTAL_WIDTH_IN_DAYS)
        self.__missed_rentals__ = Rental.objects.filter(
            Q(
                Q(collection_date__gte=__start_date__) &
                Q(collection_date__lt=__end_date__)
            ) &
            Q(is_deleted=False, collection_status=Rental.ACTIVE)
        )
