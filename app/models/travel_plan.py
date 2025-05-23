from app import db
from datetime import datetime

class TravelPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    dest_lat = db.Column(db.Float)  # 目的地纬度
    dest_lng = db.Column(db.Float)  # 目的地经度
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    budget = db.Column(db.Float)
    interests = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    itinerary_items = db.relationship('ItineraryItem', backref='travel_plan', lazy='dynamic', cascade="all, delete-orphan")
    shared_with = db.relationship('PlanShare', backref='travel_plan', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<TravelPlan {self.title}>'

class ItineraryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer, nullable=False)
    time = db.Column(db.String(10))
    activity = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    cost = db.Column(db.Float)
    notes = db.Column(db.Text)
    travel_plan_id = db.Column(db.Integer, db.ForeignKey('travel_plan.id'), nullable=False)
    
    def __repr__(self):
        return f'<ItineraryItem {self.activity}>'

class PlanShare(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    travel_plan_id = db.Column(db.Integer, db.ForeignKey('travel_plan.id'), nullable=False)
    shared_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    can_edit = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    shared_user = db.relationship('User')

    def __repr__(self):
        return f'<PlanShare plan_id={self.travel_plan_id} user_id={self.shared_user_id} status={self.status}>'
