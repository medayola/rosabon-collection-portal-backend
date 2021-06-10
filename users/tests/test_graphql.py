from django.contrib.auth import get_user_model
from django.test import TestCase

from graphene.test import Client
from paystackcollection.schema import schema


class MockUser:

    def __init__(self, user):
        self.id = user.id
        self.user = user

    def is_authenticated(self):
        return True


class MockContext:

    def __init__(self, user):
        self.user = MockUser(user)


class UserAppTest(TestCase):

    @staticmethod
    def authenticate_user(client, username, password):

        query = '''
            mutation TokenAuth($username: String!, $password: String!) {
                tokenAuth(username: $username, password: $password) {
                    token
                }
            }
        '''
        
        return []
        # return executed['data']['tokenAuth']

    def setUp(self):
        self.client = Client(schema)

    def test_can_authenticate(self):
        # user = get_user_model().objects.create(
        #     username="username", password="passcode-101")
        # query = '''
        #     mutation TokenAuth($username: String!, $password: String!) {
        #         tokenAuth(username: $username, password: $password) {
        #             token
        #         }
        #     }
        # '''

        # executed = self.client.execute(query, variable_values={
        #     "username": "username",
        #     "password": "passcode-101"
        # })
        # print('auth: ', executed)
        return []
        # return executed['data']['tokenAuth']
