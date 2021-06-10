from django.contrib import admin

# Register your models here.
from staff.models import PasswordReset
from staff.models import Staff
from staff.models import StaffCategory

admin.site.register(PasswordReset)
admin.site.register(Staff)
admin.site.register(StaffCategory)
