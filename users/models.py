import hashlib
from django.contrib.auth.models import User
from django.db import models
import random


class Person(models.Model):

    MALE = "M"
    FEMALE = "F"
    COPORATE = "C"
    GENDER = (
        (MALE, "MALE"),
        (FEMALE, "FEMALE"),
        (COPORATE, "CORPORATE ENTITY"),
    )

    CUSTOMER = "C"
    STAFF = "S"
    PERSON_TYPES = (
        (CUSTOMER, "CUSTOMER"),
        (STAFF, "STAFF"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tel = models.CharField(
        max_length=100,
        default="",
        null=True,
        blank=True
    )
    gender = models.CharField(
        max_length=2,
        choices=GENDER,
        default=MALE
    )
    person_type = models.CharField(
        max_length=2,
        choices=PERSON_TYPES,
        default=STAFF
    )

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def hashed_key(self):
        try:
            value = random.randint(99999, 999999)
            email = f"{self.user.email.strip()}{value}".encode("utf-8")
            m = hashlib.md5()
            m.update(email)
            return m.hexdigest()
        except Exception:
            return None

    class Meta:
        verbose_name = "person"
        verbose_name_plural = "persons"
        unique_together = ("user__email", "tel")
        abstract = True

    def __str__(self):
        return self.user.email
