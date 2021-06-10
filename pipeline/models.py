from django.contrib.auth.models import Group
from django.db import models
from django.utils import timezone

from mandates.models import Mandate
from staff.models import Staff
from django.contrib.postgres.fields import ArrayField

# Create your models here.


class FormStage(models.Model):
    """
    Model to show the form stage
    """

    class Meta:
        ordering = ["rank"]
        verbose_name = "form stage"
        verbose_name_plural = "form stages"

    def __str__(self):
        return "{} ({})".format(self.name, self.actor.name)

    actor = models.ForeignKey(
        Group, related_name="form_stages", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100, blank=False, null=False)
    rank = models.IntegerField(default=1)

    # buttons
    show_approve_button = models.BooleanField(default=False)
    show_decline_button = models.BooleanField(default=False)
    show_save_button = models.BooleanField(default=False)
    show_cancel_button = models.BooleanField(default=False)

    # can edit the form
    can_edit_form = models.BooleanField(default=False)
    show_payment_details = models.BooleanField(default=False)
    is_customer_stage = models.BooleanField(default=False)

    # timestamps
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FormType(models.Model):
    """
    Form Type Model
    """

    MANDATE = "MANDATE"
    STOP_MANDATE = "STOP_MANDATE"
    RENTAL = "RENTAL"

    TYPES = [
        (MANDATE, "MANDATE FORM"),
        (RENTAL, "RENTAL FORM"),
        (STOP_MANDATE, "STOP MANDATE FORM"),
    ]

    def __str__(self):
        """
        string representation of Mandate
        """
        return "{}".format(self.name)

    class Meta:
        ordering = ["created_at"]

    name = models.CharField(
        choices=TYPES,
        default=MANDATE,
        max_length=100,
        null=False,
        blank=False,
        unique=True,
    )
    stages = models.ManyToManyField(FormStage, related_name="form_types")

    # timestamps
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class MandateReview(models.Model):
    """
    Model to hold a mandate review
    """

    def foward(self):
        self.current_position += 1
        limit = 0
        if self.form_type:
            limit = self.form_type.stages.count()
            self.current_position = min(self.current_position, limit)
            self.current_position = max(self.current_position, 0)

    def backward(self):
        self.current_position -= 1
        limit = 0
        if self.form_type:
            limit = self.form_type.stages.count()
            if limit == 0:
                self.current_position = 0
            self.current_position = max(self.current_position, 0)

    def __str__(self):
        """
        string representation of Mandate Review
        """
        if self.mandate:
            customer = self.mandate.customer.name()
        else:
            customer = ""
        return "{} for {} is active:{}".format(
            self.form_type.name, customer, self.active
        )

    class Meta:
        ordering = ["created_at"]

    mandate = models.ForeignKey(
        to=Mandate,
        related_name="mandate_reviews",
        on_delete=models.CASCADE,
        null=True
    )
    form_type = models.ForeignKey(
        FormType,
        related_name="mandate_reviews",
        on_delete=models.CASCADE
    )
    active = models.BooleanField(default=True)

    current_position = models.IntegerField(default=1)

    # rentals
    rentals_to_manual = ArrayField(
        models.CharField(
            max_length=100,
            blank=False,
            null=False
        ),
        blank=True,
        null=True
    )

    # code such as rrr code for remita
    code = models.CharField(max_length=100, blank=True, null=True)

    # access code such as extra code field
    code_url = models.CharField(max_length=200, blank=True, null=True)

    # authorization code for paystack
    authorization_code = models.CharField(
        max_length=200, blank=True, null=True)

    # timestamps
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PaymentDetail(models.Model):
    class Meta:
        ordering = [
            "id",
        ]
        verbose_name = "payment detail"
        verbose_name_plural = "payment details"

    def __str__(self):
        return "{}".format(self.mandate_review.mandate)

    mandate_review = models.ForeignKey(
        MandateReview, related_name="payment_details", on_delete=models.CASCADE
    )
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    issuer = models.CharField(max_length=100, blank=True, null=True)
    card_brand = models.CharField(max_length=100, blank=True, null=True)

    # timestamps
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ReviewComment(models.Model):
    """
    Model to hold comments for Mandate reviews
    """

    class Meta:
        ordering = ["-id"]
        verbose_name = "review comment"
        verbose_name_plural = "reivew comments"

    def __str__(self):
        return "{}".format(self.comment)

    comment = models.CharField(max_length=200)
    actor = models.ForeignKey(
        to=Staff,
        related_name="mandate_review_comments",
        on_delete=models.CASCADE,
        blank=True,
        null=True)
    mandate_review = models.ForeignKey(
        to=MandateReview,
        related_name="comments",
        on_delete=models.CASCADE
    )

    # timestamps
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PaystackQueue(models.Model):

    batch_id = models.IntegerField()
    status = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}: {self.created_at} = {self.status}"

    class Meta:
        verbose_name = "paystack queue item"
        verbose_name_plural = "paystack queue items"
