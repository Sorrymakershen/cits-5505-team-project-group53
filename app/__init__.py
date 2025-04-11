from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    # 创建应用实例
    app = Flask(__name__)
    
    # 配置应用
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_travel_planning')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel_planner.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化插件
    db.init_app(app)
    login_manager.init_app(app)
    
    # 注册蓝图
    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.plan_routes import plan_bp
    from app.routes.share_routes import share_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(plan_bp)
    app.register_blueprint(share_bp)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app
