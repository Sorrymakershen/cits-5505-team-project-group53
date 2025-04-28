# filepath: c:\Users\shenx\Desktop\cits-5505-team-project-group53\app\routes\__init__.py
# This file marks the routes directory as a Python package
# It can be used to expose specific objects from modules to simplify imports

from app.routes.auth import auth_bp
from app.routes.planner import planner_bp
from app.routes.memories import memories_bp
from app.routes.main import main_bp
from app.routes.statistics import statistics_bp

__all__ = [
    'auth_bp',
    'planner_bp',
    'memories_bp',
    'main_bp',
    'statistics_bp'
]
