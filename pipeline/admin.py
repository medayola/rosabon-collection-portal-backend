from django.contrib import admin

# Register your models here.
from pipeline.models import FormStage
from pipeline.models import FormType
from pipeline.models import PaymentDetail
from pipeline.models import MandateReview
from pipeline.models import ReviewComment
from pipeline.models import PaystackQueue

admin.site.register(FormType)
admin.site.register(FormStage)
admin.site.register(PaymentDetail)
admin.site.register(MandateReview)
admin.site.register(ReviewComment)
admin.site.register(PaystackQueue)
