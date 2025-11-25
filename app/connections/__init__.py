from flask import Blueprint

bp = Blueprint('connections', __name__)

from app.connections import routes
