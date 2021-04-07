from flask_sqlalchemy import SQLAlchemy
import datetime
from sqlalchemy import Column, Integer, String
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.dialects import postgresql
db = SQLAlchemy()


class Blog(db.Model):
    __tablename__='blog'

    id = Column(Integer, primary_key = True)
    title = Column(String, unique = True)
    created = Column(timestamp, not null, default = current_timestamp)
    content = Column(text, not null)

    def __init__(self, title, content):
        self.title = title
        self.content = content

    def __repr__(self):
        return 'id {}>'.format(self.id)

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'created': self.created,
            'content': self.content,
        }
