from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os 

# 先创建 Flask 应用实例
app = Flask(__name__)
# 配置应用
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel_planner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 然后初始化扩展
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# 导入模型，确保迁移能够检测到它们
from app.models import user, travel_plan, memory

def create_app():
    # 注册蓝图和其他设置
    # 因为主应用实例已经创建，这个函数主要用来添加配置
    
    # Import user loader function
    from app import auth
    
    # Register custom template filters
    from app.template_filters import register_filters
    register_filters(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.planner import planner_bp
    from app.routes.memories import memories_bp
    from app.routes.main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(memories_bp)
    app.register_blueprint(main_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
