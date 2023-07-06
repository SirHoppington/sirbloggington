from app.Blog.blog_routes import Blog
from app.Subscriber.subscriber_model import Subscriber
from app.Tag.tag_model import Tag
from app import db
from app.Tags_Blog.tag_blog_table import tag_blog
from app.Topic.topic_model import Topic
# Query all blog posts
def blogs_query():
    result = Blog.query.all()
    return result


#Query all subscribers:
def subscribers_query():
    result = Subscriber.query.all()
    return result


#Query all tags
def all_tags_query():
    result = Tag.query.all()
    return result



# Query all tags
def tags_query():
    result = db.session.query(Tag, Blog).filter((tag_blog.c.tag_id == Tag.id) & (tag_blog.c.blog_id == Blog.id)).all()
    return result


# Given a topic, check if it exists in the DB
def get_existing_topic(current_topic):
    topic_exists = db.session.query(Topic).filter(
                            Topic.name == current_topic).first()
    return topic_exists
    