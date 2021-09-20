from flask import Blueprint

bp = Blueprint('flask_ql', __name__)

from app.flask_ql import routes
