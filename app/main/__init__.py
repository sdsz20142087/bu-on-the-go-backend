from flask import blueprints

bp = blueprints.Blueprint('main', __name__)

from app.main import routes
