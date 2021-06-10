from django.dispatch import receiver

from customers.models import Customer
from staff.models import Staff
from utils.email import Notification
from django.db.models.signals import post_save, post_delete


@receiver(post_save, sender=Customer)
def alert_on_customer_created(sender, instance, created, **kwargs):
    if created:
        to = []
        user = instance.created_by
        if created:
            try:
                staff = Staff.objects.get(user=user)
                to.append(staff.user.email)

                underwriter = Staff.objects.get(user=instance.underwriter)
                to.append(underwriter.user.email)
                
                if staff.department.head:
                    hod = staff.department.head.user.email
                    to.append(hod)

                Notification.customer_was_created(
                    to=to, staff=staff, customer=instance)
            except Exception as e:
                print('[send_staff_email]: {}'.format(e))


@receiver(post_delete, sender=Customer)
def delete_associated_user(sender, instance, **kwargs):
    user = instance.user
    try:
        user.delete()
    except Exception as e:
        print(e)
