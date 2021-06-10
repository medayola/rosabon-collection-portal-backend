from django.test import TestCase

from pipeline.models import FormStage, FormType
from staff.tests.test_graphql import StaffAppTest


class PipelineAppTest(TestCase):
    @staticmethod
    def create_form_stage(name="sample - stage", stage="sample - stage"):
        group = StaffAppTest.create_staff_category(name=stage).group
        result, _ = FormStage.objects.get_or_create(
            actor=group, defaults={"name": name}
        )
        return result

    @staticmethod
    def create_form_type_mandate():
        form = FormType.objects.filter(name=FormType.MANDATE).first()
        if form is None:
            form = FormType.objects.create(name=FormType.MANDATE)
            form.stages.set(
                [
                    PipelineAppTest.create_form_stage(
                        name="booking", stage="admin officer"
                    ),
                    PipelineAppTest.create_form_stage(
                        name="confirmation", stage="risk officer"
                    ),
                    PipelineAppTest.create_form_stage(
                        name="approval", stage="head of department"
                    ),
                ]
            )
        return form

    @staticmethod
    def create_form_type_rental():
        form = FormType.objects.filter(name=FormType.RENTAL).first()
        
        if form is None:
            form = FormType.objects.create(name=FormType.RENTAL)
            form.stages.set(
                [
                    PipelineAppTest.create_form_stage(
                        name="booking", stage="admin officer"
                    ),
                    PipelineAppTest.create_form_stage(
                        name="confirmation", stage="risk officer"
                    ),
                    PipelineAppTest.create_form_stage(
                        name="approval", stage="head of department"
                    ),
                ]
            )
        return form

    def test_can_create_form_stage(self):
        pass

    def test_can_view_form_stage(self):
        pass

    def test_can_update_form_stage(self):
        pass

    def test_can_create_form_type(self):
        pass

    def test_can_view_form_type(self):
        pass

    def test_can_update_form_type(self):
        pass

    def test_can_create_mandate_review(self):
        pass

    def test_can_view_mandate_review(self):
        pass

    def test_can_update_mandate_review(self):
        pass

    def test_can_create_payment_detail(self):
        pass

    def test_can_view_payment_detail(self):
        pass

    def test_can_update_payment_detail(self):
        pass

    def test_can_create_review_comment(self):
        pass

    def test_can_view_review_comment(self):
        pass

    def test_can_update_review_comment(self):
        pass
