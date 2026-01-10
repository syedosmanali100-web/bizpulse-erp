"""
Earnings module - Handle profit and earnings calculations
"""

from flask import Blueprint

earnings_bp = Blueprint('earnings', __name__)

from . import routes
