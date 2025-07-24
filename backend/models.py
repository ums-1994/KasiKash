from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    user_message = db.Column(db.Text)
    assistant_response = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date)
    description = db.Column(db.String(200))
    amount = db.Column(db.Float)
    category = db.Column(db.String(100)) 