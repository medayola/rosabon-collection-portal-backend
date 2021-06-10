import datetime as dt
from utils.file_printers import PandasPrinter

from mandates.models import Mandate
from mandates.models import Trial
from mandates.models import Rental

from django.db.models import Q


class ReportGenerator:

    start_date = None
    end_date = None
    printer = None
    status = ''

    def __init__(self):
        self.end_date = dt.datetime.today()
        self.start_date = self.end_date - dt.timedelta(days=6)

        self.printer = PandasPrinter()
        """ the file creator or printer class """

    def resolve_all_mandates(self, start_date, end_date, status='ALL'):
        try:
            self.printer.data = Mandate.objects.filter(
                rentals__collection_date__range=(
                    self.start_date,
                    self.end_date
                )
            ).distinct()
            """ generate the mandates """

            self.printer.filename = 'Mandate {}_{} ({})'.format(
                self.start_date.strftime('%d-%b-%Y'),
                self.end_date.strftime('%d-%b-%Y'),
                self.status
            )
            """ generate the filename """

            self.printer.generate_mandates_report()
            """ create the report sheet """

            return True
        except Exception as exc:
            print(exc)
            return False

    def resolve_inflow_expected(self):
        try:
            self.printer.data = Rental.objects.filter(
                Q(mandate__status=Mandate.ACTIVE),
                Q(collection_date__range=(
                    self.start_date, self.end_date
                ))
            ).distinct()
            """
                get the rentals that fall before the
                period that are still pending
                and
                the mandate that fall
                between the stipulated period
            """

            self.printer.filename = '{} {}_{}'.format(
                self.status,
                self.start_date,
                self.end_date
            )
            """ generate the filename """

            self.printer.generate_excd_for_the_range()
            """ create the report sheet """
            return True
        except Exception:
            return False

    def resolve_inflow_recieved(self):
        try:
            self.printer.data = Trial.objects.filter(
                Q(rental__mandate__status=Mandate.ACTIVE),
                Q(created_at__range=(self.start_date, self.end_date)),
                status=True
            ).distinct()
            """
                get the rentals that fall before the
                period that are still pending
                and
                the mandate that fall
                between the stipulated period
            """

            self.printer.filename = '{} {}_{}'.format(
                self.status,
                self.start_date,
                self.end_date
            )
            """ generate the filename """

            self.printer.generate_recvd_for_the_range()
            """ create the report sheet """
            return True
        except Exception:
            return False

    def resolve_weekly_report(self):
        try:
            rentals = Rental.objects.filter(
                mandate__status=Mandate.ACTIVE,
                collection_date__range=(
                    self.start_date,
                    self.end_date
                )).distinct()

            """
                get the rentals that fall before the
                period that are still pending
                and
                the mandate that fall
                between the stipulated period
            """
            self.printer.data = [
                rental.mandate
                for rental in rentals.order_by('collection_date')]
            self.printer.filename = 'weekly report ({}) to ({})'.format(
                self.start_date.strftime('%d-%b-%Y'),
                self.end_date.strftime('%d-%b-%Y')
            )
            print(f'generated: {self.printer.filename}')
            """ generate the filename """

            self.printer.generate_weekly_report(
                start_date=self.start_date, end_date=self.end_date)
            return True
        except Exception as e:
            print('error: ', e)
            return False
