import graphene
import common.graphql.queries
import common.graphql.mutations


schema = graphene.Schema(query=common.graphql.queries.Query,
                         mutation=common.graphql.mutations.Mutation)
