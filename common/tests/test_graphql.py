from django.test import TestCase
from graphene.test import Client
from graphql_relay import to_global_id

from common.models import Bank, Country, Department, Product
from paystackcollection.schema import schema


class CommonAppTest(TestCase):

    @staticmethod
    def create_country(name, abbreviation):
        country = Country.objects.create(name=name, abbreviation=abbreviation)
        return country

    @staticmethod
    def create_bank(name, abbreviation):
        bank, _ = Bank.objects.get_or_create(name=name, abbreviation=abbreviation)
        return bank

    @staticmethod
    def create_department(name):
        department, _ = Department.objects.get_or_create(name=name)
        return department

    @staticmethod
    def create_product(name, gateway_code):
        product, _ = Product.objects.get_or_create(name=name, gateway_code=gateway_code)
        return product

    def setUp(self):
        self.client = Client(schema)

    def test_can_create_country(self):
        query = '''
            mutation CreateCountry {
                createCountry(input:{name:"name", abbreviation:"abbreviation"}) {
                    ok
                    country {
                        name
                        abbreviation
                    }
                }
            }
        '''
        executed = self.client.execute(query)
        executed = executed['data']['createCountry']

        self.assertEqual(executed['ok'], True)
        self.assertEqual(executed['country']['name'], 'name')
        self.assertEqual(executed['country']['abbreviation'], 'abbreviation')

    def test_can_create_bank(self):
        query = '''
            mutation CreateBank {
                createBank (input: {name: "name", abbreviation: "abbreviation"}) {
                    ok
                    bank {
                        name
                        abbreviation
                    }
                }
            }
        '''
        executed = self.client.execute(query)
        self.assertEqual({
            'ok': True,
            'bank': {
                'name': 'name',
                'abbreviation': 'abbreviation'
            }
        }, executed['data']['createBank'])

    def test_can_create_department(self):
        name = "sample name"
        query = '''
            mutation CreateDepartment {
                createDepartment (name: "sample name") {
                    success
                    department {
                        name
                    }
                }
            }
        '''
        executed = self.client.execute(query)
        self.assertEqual({
            'success': True,
            'department': {
                'name': 'sample name'
            }
        }, executed['data']['createDepartment'])

    def test_can_create_product(self):
        query = '''
            mutation CreateProduct {
                createProduct (name: "name", gatewayCode: "000001") {
                    success
                    product {
                        name
                        gatewayCode
                    }
                }
            }
        '''
        executed = self.client.execute(query)
        self.assertEqual({
            'success': True,
            'product': {
                'name': 'name',
                'gatewayCode': '000001'
            }
        }, executed['data']['createProduct'])

    def test_can_update_country(self):
        country = CommonAppTest.create_country(
            name='name', abbreviation='abbreviation')

        query = '''
            mutation UpdateCountry ($id:ID!, $input:CountryInput!) {
                updateCountry(id: $id, input:$input) {
                    ok
                    country {
                        name
                        abbreviation
                    }
                }
            }
        '''
        executed = self.client.execute(query, variable_values={
            'id': to_global_id("CountryType", country.id),
            'input': {
                'name': 'new name'
            }
        })
        self.assertEqual({
            'ok': True,
            'country': {
                'name': 'new name',
                'abbreviation': 'abbreviation'
            }
        }, executed['data']['updateCountry'])

    def test_can_update_bank(self):
        bank = CommonAppTest.create_bank(
            name="bank", abbreviation="abbreviation")
        query = '''
            mutation UpdateBank($id: ID!, $input: BankInput!){
                updateBank (id: $id, input:$input) {
                    ok
                    bank {
                        name
                        abbreviation
                    }
                }
            }
        '''
        executed = self.client.execute(query, variable_values={
            "id": to_global_id("BankType", bank.id),
            "input": {
                "name": "name"
            }
        })
        self.assertEqual({
            'ok': True,
            'bank': {
                'name': 'name',
                'abbreviation': 'abbreviation'
            }
        }, executed['data']['updateBank'])

    def test_can_update_department(self):
        department = CommonAppTest.create_department(name="department")
        query = '''
            mutation UpdateDepartment($id: ID!, $name:String!){
                updateDepartment (id: $id, name:$name) {
                    success
                    department {
                        name
                    }
                }
            }
        '''

        executed = self.client.execute(query, variable_values={
            "id": to_global_id("DepartmentType", department.id),
            "name": "sample department"
        })

        self.assertEqual({
            "success": True,
            "department": {
                "name": "sample department",
            }
        }, executed['data']['updateDepartment'])

    def test_can_update_product(self):
        product = CommonAppTest.create_product(
            name="product", gateway_code="000001")
        query = '''
            mutation UpdateProduct ($id:ID!, $name:String!) {
                updateProduct(id:$id, name:$name) {
                    success
                    product {
                        name
                    }
                }
            }
        '''

        executed = self.client.execute(query, variable_values={
            "id": to_global_id("ProductType", product.id),
            "name": "new product"
        })

        self.assertEqual({
            "success": True,
            "product": {
                "name": "new product"
            }
        }, executed['data']['updateProduct'])

    def test_can_view_country(self):
        country = CommonAppTest.create_country(
            name="Nigeria", abbreviation="NG")
        query = '''
            query Country($id:ID!){
                country (id: $id) {
                    name
                    abbreviation
                }
            }
        '''

        executed = self.client.execute(query, variable_values={
            "id": to_global_id("CountryType", country.id)
        })

        self.assertEqual({
            "name": country.name,
            "abbreviation": country.abbreviation,
        }, executed['data']['country'])

    def test_can_view_bank(self):
        bank = CommonAppTest.create_bank(name="bank", abbreviation="b")
        query = '''
            query Bank($id:ID!){
                bank (id: $id) {
                    name
                    abbreviation
                }
            }
        '''

        executed = self.client.execute(query, variable_values={
            "id": to_global_id("BankType", bank.id)
        })
        self.assertEqual({
            "name": bank.name,
            "abbreviation": bank.abbreviation
        }, executed['data']['bank'])

    def test_can_view_department(self):
        department = CommonAppTest.create_department(name="department")

        query = '''
            query Department($id:ID!){
                department (id: $id) {
                    name
                }
            }
        '''

        executed = self.client.execute(query, variable_values={
            "id": to_global_id("DepartmentType", department.id)
        })

        self.assertEqual({
            "name": department.name
        }, executed['data']['department'])

    def test_can_view_product(self):
        product = CommonAppTest.create_product(
            name="product", gateway_code="00001")
        query = '''
            query Product($id:ID!){
                product (id: $id) {
                    name
                    gatewayCode
                }
            }
        '''

        executed = self.client.execute(query, variable_values={
            "id": to_global_id("ProductType", product.id)
        })

        self.assertEqual({
            "name": product.name,
            "gatewayCode": product.gateway_code,
        }, executed['data']['product'])
