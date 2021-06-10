from django.db import models


# Create your models here.


class Country(models.Model):
    name = models.CharField(max_length=200, unique=True)
    abbreviation = models.CharField(max_length=100, null=True, blank=True)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateField(blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.name.lower())

    class Meta:
        ordering = ('-created_at', )
        verbose_name_plural = 'countries'
        verbose_name = 'country'


class State(models.Model):
    name = models.CharField(max_length=200, unique=True)
    abbreviation = models.CharField(max_length=100, null=True, blank=True)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateField(blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.name.lower())

    class Meta:
        ordering = ('-created_at', )


class Bank(models.Model):

    name = models.CharField(max_length=200, unique=True)
    abbreviation = models.CharField(max_length=100, null=True, blank=True)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateField(blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.name.title())

    class Meta:
        ordering = ('name',  'abbreviation', )
        verbose_name_plural = 'banks'
        verbose_name = 'bank'


class Department(models.Model):

    class Meta:
        ordering = ('-name', )

    def __str__(self):
        """
        string representation of the department model
        """
        return '{} department.'.format(self.name)

    name = models.CharField(max_length=100, unique=True)
    head = models.OneToOneField(
        to='staff.Staff',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='head_of_department')

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Product(models.Model):

    class Meta:
        ordering = ['name']
        verbose_name = 'collectiojn product'
        verbose_name_plural = 'collection products'

    def __str__(self):
        """
        string representation of the product model
        """
        return '{}'.format(self.name).upper()

    name = models.CharField(max_length=100)
    gateway_code = models.CharField(max_length=100, default='', null='')

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Branch(models.Model):
    name = models.CharField(max_length=100)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'branches'

    def __str__(self):
        """
        string representation of the branch model
        """
        return self.name
