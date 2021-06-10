import django_filters
from django.db.models import Q

from customers.models import Customer


class CustomerFilter(django_filters.FilterSet):
    search_text = django_filters.CharFilter(method='filter_search_text')

    class Meta:
        model = Customer
        fields = []

    def filter_search_text(self, queryset, name, value):
        for text in value.split():
            queryset &= queryset.filter(
                Q(user__email__icontains=text) |
                Q(company_name__icontains=text) |
                Q(user__first_name__icontains=text) |
                Q(user__last_name__icontains=text)
            )
        return queryset.distinct()
