
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
