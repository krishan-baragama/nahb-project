"""
Level 10 Models - Story, Page, Choice
"""
from app import db
from datetime import datetime


class Story(db.Model):
    __tablename__ = 'stories'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='published')
    start_page_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    pages = db.relationship('Page', backref='story', lazy=True, foreign_keys='Page.story_id')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'start_page_id': self.start_page_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Page(db.Model):
    __tablename__ = 'pages'
    
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_ending = db.Column(db.Boolean, default=False)
    ending_label = db.Column(db.String(100), nullable=True)  # Level 13
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    choices = db.relationship('Choice', foreign_keys='Choice.page_id', backref='page', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_choices=True):
        result = {
            'id': self.id,
            'story_id': self.story_id,
            'text': self.text,
            'is_ending': self.is_ending,
            'ending_label': self.ending_label
        }
        if include_choices:
            result['choices'] = [c.to_dict() for c in self.choices]
        return result


class Choice(db.Model):
    __tablename__ = 'choices'
    
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    next_page_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    next_page = db.relationship('Page', foreign_keys=[next_page_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'next_page_id': self.next_page_id
        }