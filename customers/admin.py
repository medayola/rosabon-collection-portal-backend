from django.contrib import admin

from customers.models import Customer
from customers.models import BankingDetail

# Register your models here.
admin.site.register(Customer)
admin.site.register(BankingDetail)
