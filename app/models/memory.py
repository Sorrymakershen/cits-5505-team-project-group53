from app import db
from datetime import datetime

class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    visit_date = db.Column(db.DateTime)
    description = db.Column(db.Text)
    emotional_rating = db.Column(db.Integer)  # 1-5 scale for emotional impact
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    photos = db.relationship('Photo', backref='memory', lazy='dynamic', cascade="all, delete-orphan")
    tags = db.relationship('MemoryTag', backref='memory', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Memory {self.title}>'

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(200))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    memory_id = db.Column(db.Integer, db.ForeignKey('memory.id'), nullable=False)
    
    def __repr__(self):
        return f'<Photo {self.filename}>'

class MemoryTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    memory_id = db.Column(db.Integer, db.ForeignKey('memory.id'), nullable=False)
    
    def __repr__(self):
        return f'<MemoryTag {self.name}>'
