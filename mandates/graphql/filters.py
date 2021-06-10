import django_filters
from django.db.models import Q

from mandates.models import Mandate


class MandateFilter(django_filters.FilterSet):
    """
    Filter class for Mandate Model
    The class filters by
    [-] customer: string containing customer name or email address
    [-] status: string containing the status of mandates required
    [-] tenure: string with amount of months required
    """

    customer = django_filters.CharFilter(method='filter_by_customer')
    status = django_filters.CharFilter(method='filter_by_status')
    tenure = django_filters.CharFilter(method='filter_by_tenure')

    class Meta:
        model = Mandate
        fields = []

    def filter_by_customer(self, queryset, name, value):
        data = queryset.filter(
            Q(customer__user__first_name__icontains=value) |
            Q(customer__user__last_name__icontains=value) |
            Q(customer__user__email__icontains=value)
        )
        """ method to filter mandate by customer name """
        return data

    def filter_by_status(self, queryset, name, value):
        return queryset.filter(status__iexact=value)
        """ method to filter mandate by status """

    def filter_by_tenure(self, queryset, name, value):
        return queryset.filter(tenure=value)
        """ method to filter mandate by tenure """
