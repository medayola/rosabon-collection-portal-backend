import graphene

import common.graphql.queries
import customers.graphql.queries
import mandates.graphql.queries
import gateways.graphql.queries
import staff.graphql.queries
import pipeline.graphql.queries

import common.graphql.mutations
import customers.graphql.mutations
import mandates.graphql.mutations
import gateways.graphql.mutations
import staff.graphql.mutations
import users.schema

# forms
import utils.forms.mandate_form


# schema Query
class Query(users.schema.Query, common.graphql.queries.Query,
            customers.graphql.queries.Query,
            mandates.graphql.queries.Query,
            gateways.graphql.queries.Query,
            staff.graphql.queries.Query,
            pipeline.graphql.queries.Query,
            utils.forms.mandate_form.MandateForm,
            graphene.ObjectType):
    pass


# Schema Mutation
class Mutation(common.graphql.mutations.Mutation,
               customers.graphql.mutations.Mutation,
               mandates.graphql.mutations.Mutation,
               gateways.graphql.mutations.Mutation,
               staff.graphql.mutations.Mutation,
               users.schema.Mutation,
               graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
