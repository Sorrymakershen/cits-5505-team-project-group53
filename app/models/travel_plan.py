from app import db
from datetime import datetime
import json

class TravelPlan(db.Model):
    """旅行计划模型，存储用户创建的旅行计划"""
    __tablename__ = 'travel_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    budget = db.Column(db.Float)
    preferences = db.Column(db.Text)  # 存储JSON格式的偏好数据
    itinerary = db.Column(db.Text)    # 存储JSON格式的行程数据
    budget_allocation = db.Column(db.Text)  # 存储JSON格式的预算分配数据
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键关联到创建者
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # 计划的共享关系
    shares = db.relationship('PlanShare', backref='travel_plan', lazy='dynamic')
    
    def set_preferences(self, preferences_dict):
        """设置旅行偏好为JSON格式"""
        self.preferences = json.dumps(preferences_dict)
        
    def get_preferences(self):
        """获取旅行偏好数据"""
        return json.loads(self.preferences) if self.preferences else {}
    
    def set_itinerary(self, itinerary_dict):
        """设置行程为JSON格式"""
        self.itinerary = json.dumps(itinerary_dict)
        
    def get_itinerary(self):
        """获取行程数据"""
        return json.loads(self.itinerary) if self.itinerary else {}
    
    def set_budget_allocation(self, budget_dict):
        """设置预算分配为JSON格式"""
        self.budget_allocation = json.dumps(budget_dict)
        
    def get_budget_allocation(self):
        """获取预算分配数据"""
        return json.loads(self.budget_allocation) if self.budget_allocation else {}
    
    def __repr__(self):
        return f'<TravelPlan {self.title} to {self.destination}>'


class PlanShare(db.Model):
    """旅行计划共享模型，管理计划的共享关系"""
    __tablename__ = 'plan_shares'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('travel_plans.id'))
    shared_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    shared_with_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    permission = db.Column(db.String(20), default='view')  # 'view' 或 'edit'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 共享用户关系
    shared_by = db.relationship('User', foreign_keys=[shared_by_id], backref='shared_plans')
    
    def __repr__(self):
        return f'<PlanShare plan:{self.plan_id} from:{self.shared_by_id} to:{self.shared_with_id}>'
