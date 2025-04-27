from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from app.models.travel_plan import TravelPlan
from app.models.memory import Memory
from datetime import datetime
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page with introduction to the platform features"""
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard view showing both travel plans and memories"""
    # Get upcoming travel plans (where start_date is in the future)
    upcoming_trips = TravelPlan.query.filter_by(user_id=current_user.id).filter(
        TravelPlan.start_date >= datetime.utcnow()
    ).order_by(TravelPlan.start_date).limit(6).all()
    
    # Count unique destinations
    destinations = TravelPlan.query.filter_by(user_id=current_user.id).with_entities(
        func.count(func.distinct(TravelPlan.destination))
    ).scalar() or 0
    
    # Get recent memories
    recent_memories = Memory.query.filter_by(user_id=current_user.id).order_by(
        Memory.created_at.desc()
    ).limit(6).all()
    
    return render_template(
        'dashboard.html',
        upcoming_trips=upcoming_trips,
        recent_memories=recent_memories,
        destinations=destinations
    )

@main_bp.route('/about')
def about():
    """About page with information about the platform"""
    return render_template('about.html')

@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    return render_template('terms.html')

