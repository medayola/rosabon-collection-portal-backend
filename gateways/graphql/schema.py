import graphene

import gateway.graphql.queries
import gateway.graphql.mutations


schema = graphene.Schema(query=payment_gateway.graphql.queries.Query)
