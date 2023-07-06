import os
from flask import Blueprint, request, jsonify, make_response, render_template, render_template_string, current_app, send_from_directory
from flask_login import login_required
from app import db
from app import mail
from app.Blog.blog_model import Blog
from app.Tag.tag_model import Tag
from app.Topic.topic_model import Topic
from app.Series.series_model import Series
from app.Tags_Blog.tag_blog_table import tag_blog, topic_blog, series_blog
from app.Subscriber.subscriber_model import Subscriber
from app.forms import AddBlog
from app.queries import blogs_query, subscribers_query, all_tags_query, tags_query, get_existing_topic
from datetime import timedelta
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Message
import markdown
from app.utilities.model_utilities import add_series


blogs = Blueprint('blogs', __name__)

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def my_renderer(text):
    """Inject markdown renderering into jinja template"""
    rendered_body = render_template_string(text)
    pygmented_body = markdown.markdown(rendered_body, extensions=['codehilite', 'fenced_code'])
    return pygmented_body

@blogs.route('/blog_added')
def blog_added():
    return render_template("blog_added.html")


@blogs.route('/add_blog', methods=["POST", "GET"])
@login_required
def create_blog():
    blogs = blogs_query()
    subscribers = subscribers_query()
    all_tags = all_tags_query()
    all_topics = Topic.query.all()
    latest = sorted(blogs, reverse=True, key=lambda b: b.created_at)
    form = AddBlog()
    #if form.validate_on_submit():
    if request.method == "POST":
        new_title = Blog.query.filter_by(title=form.title.data).first()
        if new_title:
            resp = jsonify({'message': 'Title already in use.'})
            resp.status_code = 400
            return resp
            # add a search to check if tag already exists.
        else:
            try:
                #Add feature image:
                file = request.files['file']
                filename1 = secure_filename(file.filename)
                file.save(os.path.join('app/static/imgs', filename1))

                #Add thumbnail:
                thumbnail = request.files['thumbnail']
                thumbnail_file = secure_filename(thumbnail.filename)
                thumbnail.save(os.path.join('app/static/imgs', thumbnail_file))
                tags = request.form.getlist('tags[]')
                new_blog = Blog(title=form.title.data, content=form.contentcode.data, summary=form.summary.data, feature_image=filename1, thumbnail=thumbnail_file)
                db.session.add(new_blog)
                for tag in tags:
                    tag_exists = db.session.query(Tag).filter(
                        Tag.name == tag).first()
                    if tag_exists:
                        new_blog.tags.append(tag_exists)
                    else:
                        # add a create tag function
                        new_tag = Tag(name=tag)
                        new_blog.tags.append(new_tag)
                        db.session.add(new_tag)
                if form.series.data != None:
                    add_series(form.series.data, new_blog)
                topic_exists = db.session.query(Topic).filter(
                    Topic.name == form.topic.data).first()
                if topic_exists:
                    new_blog.topics.append(topic_exists)
                else:
                    new_topic = Topic(name=form.topic.data)
                    new_blog.topics.append(new_topic)
                    db.session.add(new_topic)
                db.session.commit()
                id = db.session.query(Blog.id).filter(
                    Blog.title == form.title.data).first()
                idInt = str(id).replace('(', '').replace(',', '').replace(')', '')
                with mail.connect() as conn:
                    for subscriber in subscribers:
                        message = 'A new blog has been posted head over to www.hopnets.co.uk/blog/{}'.format(idInt)
                        subject = 'Hopnets Blog time!'
                        msg = Message(recipients=[subscriber.email],
                                      body=message,
                                      subject=subject)
                        conn.send(msg)
                return "Great success new post saved with ID: {}".format(idInt)
            except Exception as e:
                return(str(e))
    elif request.is_json:
        alltags = request.get_json()
        taglist = [tag for tag in alltags['values']]
        #return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    return render_template("add_blog.html",
                           form=form, blogs=latest[:4], all_topics=all_topics)


@blogs.route('/robots.txt')
def static_from_root():
    return send_from_directory(current_app.static_folder, request.path[1:])


@blogs.route('/sitemap.xml', methods=['GET'])
def sitemap():
    try:
      """Generate sitemap.xml. Makes a list of urls and date modified."""
      pages=[]
      ten_days_ago=(datetime.now() - timedelta(days=7)).date().isoformat()
      # static pages
      for rule in current_app.url_map.iter_rules():
          if "GET" in rule.methods and len(rule.arguments)==0:
              pages.append(
                           ["https://hopnets.com"+str(rule.rule),ten_days_ago]
                           )

      sitemap_xml = render_template('sitemap.xml', pages=pages)
      response= make_response(sitemap_xml)
      response.headers["Content-Type"] = "application/xml"

      return response
    except Exception as e:
        return(str(e))


@blogs.route('/', methods=["GET"])
def get_all_blogs():
    blogs = blogs_query()
    all_tags = all_tags_query()
    all_topics = Topic.query.all()
    tags = tags_query()
    latest = sorted(blogs, reverse=True, key=lambda b: b.created_at)
    if len(latest) == 0:
        return "No Blogs posted."
    else:
        return render_template('index.html', blogs=latest[:10],
                               tags=tags, homepage=latest[1:9], featured=latest[0], all_topics=all_topics)


@blogs.route('/blog/<title>', methods=["GET"])
def get_single_blog(title):

    blogs = blogs_query()
    all_topics = Topic.query.all()

    latest = sorted(blogs, reverse=True, key=lambda b: b.created_at)
    blog = db.session.query(Blog.title, Blog.content, Blog.feature_image,
                            Blog.created_at, Tag.name).filter(Blog.title == title).first()
    id = db.session.query(Blog).filter(Blog.title == title).first()
    current_series= db.session.query(Series).filter((series_blog.c.blog_id == id.id) & (series_blog.c.series_id == Series.id)).first()
    all_tags = Tag.query.all()
    html = my_renderer(blog.content)
    query_tags = db.session.query(Tag.name).filter(
        (tag_blog.c.blog_id == id.id) & (tag_blog.c.tag_id == Tag.id)).all()
    middle_index = len(query_tags)//2
    if current_series:
        current_series_id = current_series.id
    else:
        current_series_id = None
    current_topic = db.session.query(Topic).filter((topic_blog.c.blog_id == id.id) & (topic_blog.c.topic_id == Topic.id)).first()
    query_series = db.session.query(Blog).filter(
        (series_blog.c.series_id==current_series_id) & (series_blog.c.blog_id == Blog.id)).all()
    related_topic = db.session.query(Blog).filter(
        (topic_blog.c.blog_id == Blog.id) & (topic_blog.c.topic_id == current_topic.id)).all()
    return render_template('blog_post.html', blog=blog, blogs=latest[:10], html=html,
                           query_tags=query_tags, first_half_tags=query_tags[:middle_index],
                           second_half_tags=query_tags[middle_index:], all_topics=all_topics, title=title, blog_series=query_series, series=current_series, related_topic=related_topic)


@blogs.route('/topic/<topic>', methods=["GET"])
def get_topic(topic):
    blogs = Blog.query.all()
    all_topics = Topic.query.all()
    latest = sorted(blogs, reverse=True, key=lambda b: b.created_at)
    topic = db.session.query(Topic).filter(
        Topic.name == topic).first()
    query_blogs = db.session.query(Blog).filter(
        (topic_blog.c.blog_id == Blog.id) & (topic_blog.c.topic_id == Topic.id)).filter(Topic.name == topic.name).all()
    #query_blogs = topic_filter(topic)
    latest_topic = sorted(query_blogs, reverse=True, key=lambda b: b.created_at)
    tags = db.session.query(Tag, Blog).filter((tag_blog.c.tag_id == Tag.id) & (tag_blog.c.blog_id == Blog.id)).all()
    return render_template('topic_posts.html', topic=topic, tags=tags, blogs=latest[:10],query_blogs=latest_topic, all_topics=all_topics)



@blogs.route('/<tag>', methods=["GET"])
def get_tags(tag):
    blogs = Blog.query.all()
    all_tags = Tag.query.all()
    all_topics = Topic.query.all()
    latest = sorted(blogs, reverse=True, key=lambda b: b.created_at)
    tag = db.session.query(Tag).filter(
        Tag.name == tag).first()
    query_blogs = db.session.query(Blog).filter(
        (tag_blog.c.blog_id == Blog.id) & (tag_blog.c.tag_id == Tag.id)).filter(Tag.name == tag.name).all()
    latest_tag = sorted(query_blogs, reverse=True, key=lambda b: b.created_at)
    tags = db.session.query(Tag, Blog).filter((tag_blog.c.tag_id == Tag.id) & (tag_blog.c.blog_id == Blog.id)).all()
    return render_template('tag_categories.html', tag=tag, tags=tags, blogs=latest[:10],query_blogs=latest_tag, all_topics=all_topics, topics=all_tags[0:20])


#@blogs.route('/update_blog/<int:id>', methods=["POST", "GET"])
@blogs.route('/update_blog/<title>', methods=["POST", "GET"])
@login_required
def update_blog(title):
    blogs = Blog.query.all()
    subscribers = Subscriber.query.all()
    all_tags = Tag.query.all()
    all_topics = Topic.query.all()
    latest = sorted(blogs, reverse=True, key=lambda b: b.created_at)
    blog = Blog.query.filter_by(title=title).first()
    current_series = db.session.query(Series.name).filter(
        (series_blog.c.blog_id == blog.id) & (series_blog.c.series_id == Series.id)).first()
    
    topic = db.session.query(Topic.name).filter(
        (topic_blog.c.blog_id == blog.id) & (topic_blog.c.topic_id == Topic.id)).first()

    q_tags = db.session.query(Tag).filter(
        (tag_blog.c.blog_id == blog.id) & (tag_blog.c.tag_id == Tag.id)).all()
    query_tags = db.session.query(Tag.name).filter(
        (tag_blog.c.blog_id == blog.id) & (tag_blog.c.tag_id == Tag.id)).all()
    existing_tags = db.session.query(Tag, Blog).filter((tag_blog.c.tag_id == Tag.id) & (tag_blog.c.blog_id == Blog.id)).all()
    form = AddBlog()
    #if form.validate_on_submit():
    if request.method == "POST":
            try:
                print (blog.thumbnail)
                # create function
                if request.files:
                    print(request.files)
                    for x in request.files:
                        if x == 'file':
                            file = request.files['file']
                            filename = secure_filename(file.filename)
                            file.save(os.path.join('app/static/imgs', filename))
                            blog.feature_image = filename
                        if x == 'thumbnail':
                            #create function
                            thumbnail = request.files['thumbnail']
                            thumbnail_file = secure_filename(thumbnail.filename)
                            thumbnail.save(os.path.join('app/static/imgs', thumbnail_file))
                            blog.thumbnail = thumbnail_file
                if blog.title != form.title.data:
                    blog.title = form.title.data
                if blog.content != form.contentcode.data:
                    blog.content = form.contentcode.data
                if blog.summary != form.summary.data:
                    blog.summary = form.summary.data
                new_tags = request.form.getlist('tags[]')

                for current_tag in q_tags:
                    if current_tag not in new_tags:
                        blog.tags.remove(current_tag)
                    #for x in current_tag:
                    #    column = Tag.query.filter_by(name=x).first()
                    #    print(type(column))
                    #    if x not in new_tags:
                    #        blog.tags.remove(column)
                # This section causes an issue if a tag that already exists is added it removes all tags
                for tag in new_tags:
                    tag_exists = db.session.query(Tag).filter(
                        Tag.name == tag).first()
                    tag_associated = db.session.query(Tag, Blog).filter(
                        Tag.name == tag, Blog.id == blog.id).first()
                    if tag_exists:
                        blog.tags.append(tag_exists)
                    else:
                        new_tag = Tag(name=tag)
                        print(new_tag)
                        print("here")
                        blog.tags.append(new_tag)
                        db.session.add(new_tag)
                if current_series:
                    if form.series.data != current_series.name:
                        series_exists = db.session.query(Series).filter(
                            Series.name == form.series.data).first()
                        if series_exists:
                            blog.series.append(series_exists)
                        else:
                            new_series = Series(name=form.series.data)
                            blog.series.append(new_series)
                            db.session.add(new_series)
                topic_object = get_existing_topic(form.topic.data)
                print(type(topic_object))
                if topic:
                    if form.topic.data != topic.name:
                        blog.topics.append(topic_object)
                else:
                    if topic_object:
                        blog.topics.append(topic_object)
                    else:
                        new_topic = Topic(name=form.topic.data)
                        blog.topics.append(new_topic)
                        db.session.add(new_topic)
                db.session.commit()

                    #tag_exists = Tag.query.filter_by(name=tag).first()
                    #match = [x for x in query_tags if tag in x]
                    #if not tag_exists:
                    #    new_tag = Tag(name=tag)
                    #    db.session.add(new_tag)
                    #    blog.tags.append(new_tag)
                    #    db.session.commit()
                    #else:
                        #for query in query_tags:
                        #   if query.name == tag:
                        #        blog.tags.append(tag_exists)
                        #       db.session.commit()
                return "Great success post updated with ID: {}".format(blog.id)
            except Exception as e:
                return(str(e))
    elif request.is_json:
        alltags = request.get_json()
        taglist = [tag for tag in alltags['values']]
        #return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    elif request.method == "GET":
        form.title.data = blog.title
        form.summary.data = blog.summary
        if current_series:
            form.series.data = current_series.name
        if topic:
            form.topic.data = topic.name
        return render_template("update_blog.html", form=form, blogs=latest[:10], id=blog.id, blog=blog, query_tags=query_tags, all_topics=all_topics)


@blogs.route('/delete_blog/<int:id>', methods=["DELETE"])
@login_required
def delete_blog(id):
    blog = Blog.query.filter_by(id=id).first()
    db.session.delete(blog)
    db.session.commit()

    return jsonify("Blog was deleted"), 200
