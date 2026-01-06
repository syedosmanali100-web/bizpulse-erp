from flask import Blueprint

credit_bp = Blueprint('credit', __name__)

from . import routes
