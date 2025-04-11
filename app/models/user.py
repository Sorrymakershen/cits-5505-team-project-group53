from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    """用户模型，存储用户账号信息"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 用户旅行计划的关联
    travel_plans = db.relationship('TravelPlan', backref='creator', lazy='dynamic')
    
    # 用户是分享的接收者
    shared_with_me = db.relationship('PlanShare', 
                                    foreign_keys='PlanShare.shared_with_id',
                                    backref=db.backref('shared_with', lazy='joined'),
                                    lazy='dynamic')
    
    def set_password(self, password):
        """设置用户密码"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """验证用户密码"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(id):
    """用于Flask-Login加载用户"""
    return User.query.get(int(id))
