from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config
from flask_bcrypt import Bcrypt
from flask_graphql import GraphQLView
from flask_graphql_auth import GraphQLAuth
from flask_jwt_extended import JWTManager, get_jwt_identity

app = Flask(__name__)

app.config.from_object(Config)
auth = GraphQLAuth()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()
bcrypt = Bcrypt()
db.init_app(app)
migrate.init_app(app, db)
mail.init_app(app)
bcrypt.init_app(app)
auth.init_app(app)
jwt.init_app(app)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    bcrypt.init_app(app)
    auth.init_app(app)
    jwt.init_app(app)

    from app.flask_ql import bp as gql
    app.register_blueprint(gql)

    return app



