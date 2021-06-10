import django_filters
from staff.models import Staff
from django.db.models import Q


class AccountOfficerFilter(django_filters.FilterSet):
    search_text = django_filters.CharFilter(method='filter_search_text')

    class Meta:
        model = Staff
        fields = []

    def filter_search_text(self, queryset, name, value):
        for text in value.split():
            queryset &= queryset.filter(
                Q(is_account_officer=True),
                Q(user__email__icontains=value) |
                Q(user__first_name__icontains=value) |
                Q(user__last_name__icontains=value)
            )
        return queryset.distinct()
