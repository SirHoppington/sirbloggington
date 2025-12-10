from app import db
from datetime import datetime
from app.Tags_Blog.tag_blog_table import tag_blog
from slugify import slugify


class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=True)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    feature_image = db.Column(db.String)
    thumbnail = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tags = db.relationship('Tag', secondary=tag_blog, backref=db.backref('blogs_associated', lazy="dynamic"))

    user_id = db.Column(db.Integer, db.ForeignKey('user_table.id'), nullable=True)
    
    # Define the relationship
    author = db.relationship('User', back_populates='blogs')

    def __init__(self, title, content, summary, feature_image, thumbnail):
        self.title = title,
        self.slug = slugify(title),
        self.content = content,
        self.summary = summary,
        self.feature_image = feature_image,
        self.thumbnail = thumbnail

    def __repr__(self):
        return '<id {}>'.format(self.id)


    @property
    def serialize(self):
        return {
            'id' : self.id,
            'title' : self.title,
            'content' : self.content,
            'summary' : self.summary,
            'feature_image' : self.feature_image,
            'thumbnail' : self.thumbnail,
            'created_at' : self.created_at,
        }
