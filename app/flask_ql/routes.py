from flask_graphql import GraphQLView
from .queries import schema
from app.flask_ql import bp

bp.add_url_rule(
    '/graph',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True  # for having the GraphiQL interface
    )
)
