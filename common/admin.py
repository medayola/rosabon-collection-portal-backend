from django.contrib import admin

from common.models import Bank, Branch, Country, Department, Product, State

# Register your models here.
admin.site.register(Bank)
admin.site.register(Branch)
admin.site.register(Country)
admin.site.register(Department)
admin.site.register(Product)
admin.site.register(State)
