from django.conf import settings
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from staff.models import Staff, StaffCategory
from utils.email import Notification

#####################################################
#####################################################
#
# SIGNALS
#
#####################################################
#####################################################


@receiver(post_save, sender=StaffCategory)
def create_group(sender, instance, created, **kwargs):
    group, _ = Group.objects.get_or_create(
        staff_category=instance,
        defaults={'name': instance.name}
    )


# @receiver(pre_save, sender=StaffCategory)
# def create_group(sender, instance, **kwargs):
#     with transaction.atomic():
#         if instance.group is None:
#             instance.group = Group.objects.create(name=instance.name)
#         else:
#             instance.group.name = instance.name
#             instance.group.save()


@receiver(pre_save, sender=Staff)
def save_staff_user_permissions(sender, instance, **kwargs):
    with transaction.atomic():
        if instance.category is not None:
            if instance.user is not None:
                [instance.user.groups.remove(x) for x in Group.objects.all()]
                if instance.category.group:
                    instance.category.group.user_set.add(instance.user)


# send an email to a staff once the account is created
@receiver(post_save, sender=Staff)
def send_staff_email(sender, instance, created, **kwargs):
    to = [instance.user.email, ]
    if created:
        try:
            hod = instance.department.hod.user.email
            to.append(hod)
        except Exception:
            pass

        # generate a reset password
        reset_link = '{}/{}/{}'.format(
            settings.FRONT_END,
            'reset-password',
            instance.create_password_reset()
        )

        try:
            Notification.staff_added_to_system(
                to=to, staff=instance, reset_link=reset_link)
        except Exception as e:
            print('[send_staff_email]: {}'.format(e))
