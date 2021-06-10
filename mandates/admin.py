from django.contrib import admin

# Register your models here.
from mandates.models import Mandate, Trial, Rental, CustomerFee

admin.site.register(CustomerFee)
admin.site.register(Mandate)
admin.site.register(Trial)
admin.site.register(Rental)
