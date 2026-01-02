"""
Hotel management routes
COPIED AS-IS from app.py
"""

from flask import Blueprint, render_template

hotel_bp = Blueprint('hotel', __name__)

# Hotel module routes
@hotel_bp.route('/hotel/dashboard')
def hotel_dashboard():
    return render_template('hotel_dashboard.html')

@hotel_bp.route('/hotel/profile')
def hotel_profile():
    return render_template('hotel_profile.html')