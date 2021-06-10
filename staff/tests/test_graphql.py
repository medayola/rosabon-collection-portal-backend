from os.path import abspath

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.test import TestCase
from faker import Faker
from graphene.test import Client
from graphql_relay import to_global_id

from common.tests.test_graphql import CommonAppTest
from paystackcollection.schema import schema
from staff.models import Staff, StaffCategory
from users.tests.test_graphql import MockUser
from users.models import Person


class StaffAppTest(TestCase):

    @staticmethod
    def create_staff_category(name="account officer", permissions=[]):
        group, created = Group.objects.get_or_create(defaults={'name': name})
        [group.permissions.add(permission) for permission in permissions]

        if created:
            category = StaffCategory.objects.create(name=name, group=group)
        else:
            category = StaffCategory.objects.get(group=group)
        return category

    @staticmethod
    def create_account_officer():
        faker = Faker()
        first_name = faker.first_name()
        last_name = faker.last_name()
        username = faker.company_email().split('@')[0]
        password = "Passw0rd1o1"

        with transaction.atomic():
            category = StaffAppTest.create_staff_category()
            department = CommonAppTest.create_department(name="sales")
            user = get_user_model().objects.create(
                first_name=first_name,
                last_name=last_name,
                username=username,
                password=password)
            return Staff.objects.create(
                user=user,
                department=department,
                category=category
            )
        return None

    @staticmethod
    def create_staff():

        faker = Faker()
        first_name = faker.first_name()
        last_name = faker.last_name()
        username = faker.company_email().split('@')[0]
        password = "Passw0rd1o1"

        with transaction.atomic():
            category = StaffAppTest.create_staff_category()
            department = CommonAppTest.create_department(name="collections")
            user = get_user_model().objects.create(
                first_name=first_name,
                last_name=last_name,
                username=username,
                password=password)
            return Staff.objects.create(
                user=user,
                department=department,
                category=category
            )
        return None

    def setUp(self):
        self.client = Client(schema=schema)
        self.staff = StaffAppTest.create_staff()
        self.faker = Faker()

    def test_can_create_forgot_password(self):
        # when a staff request to change password

        query = '''
            mutation forgotPassword($email: String!) {
                requestForgotPassword(email: $email) {
                    ok
                }
            }
        '''
        executed = self.client.execute(
            query,
            variable_values={"email": self.staff.user.email})

        self.assertEqual({
            "ok": True
        }, executed['data']['requestForgotPassword'])

    # def test_cannot_create_forgot_password(self):
    #     # when a staff request to change password

    #     query = '''
    #         mutation forgotPassword($email: String!) {
    #             requestForgotPassword(email: $email) {
    #                 ok
    #             }
    #         }
    #     '''

    #     executed = self.client.execute(
    #         query,
    #         variable_values={"email": "anymail@sample.com"})

    #     self.assertIsNone(executed['data']['requestForgotPassword'])
    #     self.assertIn('errors', executed)

    def test_can_request_password_reset(self):
        query = '''
            mutation ResetPassword(
                $token: String!, 
                $newPassword: String!
                $oldPassword:String! ) {
                resetPassword (
                    token: $token,
                    oldPassword:$oldPassword,
                    newPassword:$newPassword) {
                        ok
                    }
                }

        '''

        token = ""
        try:
            if self.staff.user.password_reset:
                if self.staff.user.password_reset.is_set:
                    token = self.staff.user.password_reset.token
        except Exception:
            token = ""

        executed = self.client.execute(
            query,
            variable_values={
                "newPassword": "newPasscode101",
                "oldPassword": "Passw0rd1o1",
                "token": token
            })

        self.assertEqual({
            "ok": True
        }, executed['data']['resetPassword'])

    def test_can_create_staff_category(self):
        query = '''
            mutation CreateStaffCategory($name: String!) {
                createStaffCategory(name: $name) {
                    id
                    success
                }
            }
        '''

        executed = self.client.execute(
            query,
            context_value=MockUser(self.staff.user),
            variable_values={
                "name": "admin staff"
            })
        staff_category = StaffCategory.objects.all().last()
        self.assertEqual({
            "id": f"{staff_category.id}",
            "success": True
        }, executed['data']['createStaffCategory'])

    def test_can_view_staff_category(self):
        category = StaffAppTest.create_staff_category(name="sales officer")
        query = '''
            query GetStaffCategory ($id: ID!) {
                staffCategory(id:$id)  {
                    name
                    isDeleted
                }
            }
        '''
        executed = self.client.execute(
            query,
            context_value=MockUser(self.staff.user),
            variable_values={
                "id": to_global_id("StaffCategoryType", category.id)
            })

        self.assertEqual({
            "name": category.name,
            "isDeleted": category.is_deleted
        }, executed['data']['staffCategory'])

    def test_can_update_staff_category(self):
        category = StaffAppTest.create_staff_category(name="security guard")
        query = '''
            mutation UpdateStaffCategory($id:ID!, $name: String!) {
                updateStaffCategory(id:  $id, name: $name) {
                    success
                    category {
                        name
                    }
                }
            }
        '''
        executed = self.client.execute(
            query,
            context_value=MockUser(self.staff.user),
            variable_values={
                "id": to_global_id("StaffCategoryType", category.id),
                "name": "special forces"
            })

        self.assertEqual({
            "success": True,
            "category": {
                "name": "special forces"
            }
        }, executed['data']['updateStaffCategory'])

    def test_can_create_staff(self):
        category = StaffAppTest.create_staff_category(name="sales admin")
        department = CommonAppTest.create_department(name="treasury")
        query = '''
            mutation CreateStaff(
                $username: String!,
                $firstName: String!,
                $lastName: String!,
                $email: String!,
                $password: String!,
                $gender: String!,
                $category: ID!,
                $department: ID!) {
                createStaff(
                    username: $username,
                    firstName: $firstName,
                    lastName: $lastName,
                    email: $email,
                    password: $password,
                    gender: $gender,
                    department: $department,
                    category: $category) {
                        success
                        staff {
                            id
                        }
                    }
                }
        '''

        username = self.faker.company_email().split('@')[0]
        executed = self.client.execute(
            query,
            context_value=MockUser(self.staff.user),
            variable_values={
                "username": username,
                "firstName": self.faker.first_name(),
                "lastName": self.faker.last_name(),
                "email": self.faker.company_email(),
                "password": self.faker.company_email(),
                "gender": Person.MALE,
                "category": to_global_id("StaffCategoryType", category.id),
                "department": to_global_id("DepartmentType", department.id),
            })
        staff = Staff.objects.order_by('id').last()
        self.assertEqual({
            "success": True,
            "staff": {
                "id": to_global_id("StaffType", staff.id)
            }
        }, executed['data']['createStaff'])

    def test_can_view_staff(self):
        staff = StaffAppTest.create_staff()
        query = '''
            query GetStaff ($id: ID!) {
                staff(id:$id)  {
                    name
                    user {
                        firstName
                        lastName
                    }
                    isDeleted
                }
            }
        '''
        executed = self.client.execute(
            query,
            context_value=MockUser(self.staff.user),
            variable_values={
                "id": to_global_id("StaffType", staff.id)
            })

        self.assertEqual({
            "name": staff.name(),
            "user": {
                "firstName": staff.user.first_name,
                "lastName": staff.user.last_name,
            },
            "isDeleted": False,
        }, executed['data']['staff'])

    def test_can_update_staff(self):
        query = '''
            mutation UpdateStaffById(
                $id: ID!,
                $username: String,
                $firstName: String,
                $lastName: String,
                $email: String,
                $password: String,
                $gender: String,
                $category: ID,
                $department: ID) {
                updateStaff(
                    id:$id,
                    username: $username,
                    firstName: $firstName,
                    lastName: $lastName,
                    email: $email,
                    password: $password,
                    gender: $gender,
                    department: $department,
                    category: $category) {
                        success
                        staff {
                            user {
                                firstName
                            }
                        }
                    }
                }
        '''
        first_name = self.faker.first_name()
        executed = self.client.execute(
            query,
            context_value=MockUser(self.staff.user),
            variable_values={
                "id": to_global_id("StaffType", self.staff.id),
                "firstName": first_name,
            })
        self.assertEqual({
            "success": True,
            "staff": {
                "user": {
                    "firstName": first_name
                }
            }
        }, executed['data']['updateStaff'])
