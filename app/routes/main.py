from flask import Blueprint, render_template, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page with introduction to the platform features"""
    return render_template('index.html')

@main_bp.route('/dashboard')
def dashboard():
    """Dashboard view showing both travel plans and memories"""
    return render_template('dashboard.html')

@main_bp.route('/about')
def about():
    """About page with information about the platform"""
    return render_template('about.html')
