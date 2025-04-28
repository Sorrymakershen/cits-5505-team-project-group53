from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os 

# create the Flask application
app = Flask(__name__)
# configure the application
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel_planner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_CHECK_DEFAULT'] = False  
app.config['WTF_CSRF_TIME_LIMIT'] = None      

# initialize CSRF protection
csrf = CSRFProtect(app)

# initialize the database and migration
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# import models
from app.models import user, travel_plan, memory

def create_app():
    
    # Import user loader function
    from app import auth
    
    # Register custom template filters
    from app.template_filters import register_filters
    register_filters(app)
      # Register blueprints
    from app.routes import auth_bp, planner_bp, memories_bp, main_bp, statistics_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(memories_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(statistics_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
