from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    __tablename__ = 'user_table'
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(40), nullable=False)
    lastname = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120), nullable=False)
    blogs = db.relationship('Blog', back_populates='author',  lazy='dynamic')

    def __repr__(self):
        return f'<User {self.firstname}>'
