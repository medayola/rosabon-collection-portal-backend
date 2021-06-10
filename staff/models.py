from django.contrib.auth.models import Group, Permission, User
from django.db import models

from users.models import Person
from common.models import Department
# Create your models here.


class PasswordReset(models.Model):
    user = models.OneToOneField(
        User, related_name='password_reset', on_delete=models.CASCADE)

    token = models.CharField(unique=True, max_length=200, null=True)

    is_set = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} with key: {} => {}'.format(
            self.user.email,
            self.token,
            self.is_set)

    class Meta:
        verbose_name = 'password reset token'
        verbose_name_plural = 'password reset tokens'


class StaffCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    group = models.OneToOneField(
        Group,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='staff_category')

    group_email = models.CharField(
        max_length=200,
        null=True,
        blank=True)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'staff category'
        verbose_name_plural = 'staff categories'


class Staff(Person):

    is_account_officer = models.BooleanField(default=False)
    is_supervisor = models.BooleanField(default=False)
    category = models.ForeignKey(to=StaffCategory, on_delete=models.CASCADE)
    department = models.ForeignKey(
        to=Department,
        on_delete=models.CASCADE,
        related_name='staff')

    def my_permissions(self):
        permissions = []
        perms = [i.permissions.all() for i in self.user.groups.all()] + \
            [self.user.user_permissions.all()]
        for perm in perms:
            permissions.extend(perm)
        response = Permission.objects.filter(
            pk__in=[i.id for i in permissions])

        return response

    def name(self):
        return ' '.join([self.user.first_name, self.user.last_name])

    def email(self):
        return '{}'.format(self.user.email)

    class Meta:
        ordering = ('-id', )
        verbose_name = 'staff'
        verbose_name_plural = 'staff'

    def create_password_reset(self):
        # check if the staff has a password reset request
        status = False

        password_reset = PasswordReset.objects.filter(user=self.user).first()

        if password_reset:
            status = password_reset.is_set
        else:
            password_reset = PasswordReset()
            password_reset.user = self.user
            password_reset.token = self.hashed_key()

        if not status:
            password_reset.is_set = True
            password_reset.save()
        return password_reset.token

    def __str__(self):
        """
        string representation of a staff
        """
        return '{} {} of {}'.format(
            self.user.first_name.lower(),
            self.user.last_name.lower(),
            self.department)
