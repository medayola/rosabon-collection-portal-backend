from django.test import TestCase
from graphene.test import Client
from graphql_relay import to_global_id

from gateways.models import PaymentGateway
from paystackcollection.schema import schema


def create_gateway(name="remitta"):
    return PaymentGateway.objects.create(name=name)


class GatewayAppTest(TestCase):

    def setUp(self):
        self.client = Client(schema=schema)

    def test_can_create_gateway(self):
        query = '''
            mutation CreatePaymentGateway ($name:String!) {
                createGateway(name:$name) {
                    gateway {
                        name
                    }
                    success
                }
            }
        '''
        name = "remitta"
        executed = self.client.execute(query, variable_values={"name": name})
        self.assertEqual({
            "success": True,
            "gateway": {
                "name": name
            }
        }, executed['data']['createGateway'])

    def test_can_update_gateway(self):
        gateway = create_gateway()
        query = '''
            mutation UpdatePaymentGateway ($id:ID!, $name:String!) {
                updateGateway(id:$id, name:$name) {
                    success
                    gateway {
                       name
                    }
                }
            }
        '''
        name = "paystack"
        executed = self.client.execute(query, variable_values={
            "id": to_global_id("PaymentGatewayType", gateway.id),
            "name": name
        })
        self.assertEqual({
            "success": True,
            "gateway": {
                "name": name
            }
        }, executed['data']['updateGateway'])

    def test_can_view_gateway(self):
        gateway = create_gateway()
        query = '''
            query Gateway($id:ID!) {
                paymentGateway(id:$id) {
                    name
                }
            }
        '''

        executed = self.client.execute(query, variable_values={
            "id": to_global_id("PaymentGatewayType", gateway.id),
        })
        self.assertEqual({
            "name": gateway.name
        }, executed['data']['paymentGateway'])
