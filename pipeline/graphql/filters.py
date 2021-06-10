import django_filters

from django.db.models import Q

from pipeline.models import FormType, MandateReview


class MandateReviewFilter(django_filters.FilterSet):
    """
    Filter class for the MandateReview Model
    """

    by_rentals = django_filters.BooleanFilter(method='filter_by_rentals')
    by_customer = django_filters.CharFilter(method='filter_by_customer')

    def filter_by_rentals(self, queryset, name, value):
        if value is False:
            return queryset.filter(
                form_type__name=FormType.RENTAL,
                is_deleted=False,
                active=True
            )
        else:
            return queryset.filter(
                form_type__name=FormType.MANDATE,
                is_deleted=False,
                active=True
            )

    def filter_by_customer(self, queryset, name, value):
        data = queryset
        for text in value.split():
            data &= queryset.filter(
                Q(mandate__customer__company_name__icontains=text) |
                Q(mandate__customer__user__email__icontains=text) |
                Q(mandate__customer__user__first_name__icontains=text) |
                Q(mandate__customer__user__last_name__icontains=text)
            )
        return data.distinct()

    class Meta:
        model = MandateReview
        fields = []
