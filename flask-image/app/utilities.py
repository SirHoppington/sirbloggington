import re

from app.Blog.blog_model import Blog
from app.Tag.tag_model import Tag

def estimate_reading_time(text: str, WPM: int = 200) -> int:
    total_words = len(re.findall(r'\w+', text))
    time_minute = total_words // WPM + 1
    if time_minute == 0:
        time_minute = 1
    elif time_minute > 60:
        return str(time_minute // 60) + 'h'
    return str(time_minute) + ' min read'


def generate_articles():
    # example - gets all user ids from an SQLAlchemy model `User`
    blogs = Blog.query.all()
    return {"title": [blog.title for blog in blogs]}

def generate_tags():
    # example - gets all user ids from an SQLAlchemy model `User`
    tags = Tag.query.all()
    return {"tag": [tag.name for tag in tags]}