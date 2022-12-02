import os
from flask import Blueprint, request, jsonify, make_response, render_template, render_template_string, url_for, redirect, json
from flask_login import login_required, current_user
from app import db
from app import mail
from flask_jwt_extended import jwt_required
from app.Blog.blog_model import Blog
from app.Tag.tag_model import Tag
from app.Tags_Blog.tag_blog_table import tag_blog
from app.Subscriber.subscriber_model import Subscriber
from app.forms import AddBlog
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Message
import markdown
import gzip
import subprocess


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
    blogs = Blog.query.all()
    subscribers = Subscriber.query.all()
    all_tags = Tag.query.all()
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
                           form=form, blogs=latest[:4], topics=all_tags[0:20])

#    blog_id = getattr(new_blog, "id")
#    return jsonify({"id": blog_id})

@blogs.route('/test_blog', methods=["POST", "GET"])
def test_blog():
    blogs = Blog.query.all()
    latest = sorted(blogs, reverse=True, key=lambda b: b.created_at)
    form = AddBlog()
    # check if the post request has the file part
    if request.method == "POST":
        if 'files[]' not in request.files:
            resp = jsonify({'message': 'No file part in the request'})
            resp.status_code = 400
            return resp

        files = request.files.getlist('files[]')

        errors = {}
        success = False

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join('imgs', filename))
                success = True
            else:
                errors[file.filename] = 'File type is not allowed'

        if success and errors:
            errors['message'] = 'File(s) successfully uploaded'
            resp = jsonify(errors)
            resp.status_code = 206
            return resp
        if success:
            resp = jsonify({'message': 'Files successfully uploaded'})
            resp.status_code = 201
            return resp
        else:
            resp = jsonify(errors)
            resp.status_code = 400
            return resp
    return render_template("test_blog.html", form=form, blogs=latest[:10])


@blogs.route('/', methods=["GET"])
@blogs.route('/blogs', methods=["GET"])
def get_all_blogs():
    blogs = Blog.query.all()
    all_tags = Tag.query.all()
    latest = sorted(blogs, reverse=True, key=lambda b: b.created_at)
    tags = db.session.query(Tag, Blog).filter((tag_blog.c.tag_id == Tag.id) & (tag_blog.c.blog_id == Blog.id)).all()
    print("test")
    if len(latest) == 0:
        return "No Blogs posted."
    else:
        return render_template('index.html', blogs=latest[:10],
                               tags=tags, homepage=latest[1:4], featured=latest[0], topics=all_tags[0:20])

@blogs.route('/blog/<int:id>', methods=["GET"])
def get_single_blog(id):
    blogs = Blog.query.all()
    all_tags = Tag.query.all()
    latest = sorted(blogs, reverse=True, key=lambda b: b.created_at)
    blog = db.session.query(Blog.title, Blog.content, Blog.feature_image,
                            Blog.created_at, Tag.name).filter(Blog.id == id).first()
    html = my_renderer(blog.content)
    query_tags = db.session.query(Tag.name).filter(
        (tag_blog.c.blog_id == id) & (tag_blog.c.tag_id == Tag.id)).all()
    tags = db.session.query(Tag.name).filter(Blog.id == id).all()
    middle_index = len(query_tags)//2
    query_blogs = db.session.query(Blog).filter(
        (tag_blog.c.blog_id == id) & (tag_blog.c.tag_id == Tag.id)).all()

    return render_template('blog_post.html', blog=blog, blogs=latest[:10], html=html,
                           query_tags=query_tags, query_blogs=query_blogs, first_half_tags=query_tags[:middle_index],
                           second_half_tags=query_tags[middle_index:], topics=all_tags[0:20])


@blogs.route('/blog/<tag>', methods=["GET"])
def get_tags(tag):
    blogs = Blog.query.all()
    all_tags = Tag.query.all()
    latest = sorted(blogs, reverse=True, key=lambda b: b.created_at)
    tag = db.session.query(Tag.name, Tag.id).filter(
        Tag.name == tag).first()
    query_blogs = db.session.query(Blog).filter(
        (tag_blog.c.blog_id == Blog.id) & (tag_blog.c.tag_id == Tag.id)).filter(Tag.name == tag.name).all()
    latest_tag = sorted(query_blogs, reverse=True, key=lambda b: b.created_at)
    tags = db.session.query(Tag, Blog).filter((tag_blog.c.tag_id == Tag.id) & (tag_blog.c.blog_id == Blog.id)).all()
    return render_template('tag_categories.html', tag=tag, tags=tags, blogs=latest[:10],query_blogs=latest_tag, topics=all_tags[0:20])

@blogs.route('/update_blog/<int:id>', methods=["POST", "GET"])
@login_required
def update_blog(id):
    blogs = Blog.query.all()
    all_tags = Tag.query.all()
    latest = sorted(blogs, reverse=True, key=lambda b: b.created_at)
    blog = Blog.query.filter_by(id=id).first()
    query_tags = db.session.query(Tag.name).filter(
        (tag_blog.c.blog_id == id) & (tag_blog.c.tag_id == Tag.id)).all()
    form = AddBlog()
    #if form.validate_on_submit():
    if request.method == "POST":
            try:
                if request.files['file']:
                    file = request.files['file']
                    filename = secure_filename(file.filename)
                    file.save(os.path.join('static/imgs', filename))
                    blog.feature_image = filename
                tags = request.form.getlist('tags[]')
                blog.title = form.title.data
                blog.content = form.contentcode.data
                blog.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for tag in tags:
                    tag_exists = Tag.query.filter_by(name=tag).first()
                    match = [x for x in query_tags if tag in x]
                    if not tag_exists:
                        new_tag = Tag(name=tag)
                        db.session.add(new_tag)
                        blog.tags.append(new_tag)
                        db.session.commit()
                    else:
                        #for query in query_tags:
                        #   if query.name == tag:
                        #        blog.tags.append(tag_exists)
                        #       db.session.commit()
                        db.session.commit()
                    db.session.commit()
                #id = db.session.query(Blog.id).filter(
                #    Blog.title == form.title.data).first()
                #idInt = str(id).replace('(','').replace(',','').replace(')','')
                #message = "Great success new post saved with ID: {}".format(id)
                #resp = jsonify({'message': message})
                #return resp
                return "Great success new post updated with ID: {}".format(blog.id)
            except Exception as e:
                return(str(e))
    elif request.is_json:
        alltags = request.get_json()
        taglist = [tag for tag in alltags['values']]
        #return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    elif request.method == "GET":
        form.title.data = blog.title
        return render_template("update_blog.html", form=form, blogs=latest[:10], id=blog.id, blog=blog, query_tags=query_tags, topics=all_tags[0:20])

@blogs.route('/delete_blog/<int:id>', methods=["DELETE"])
@login_required
def delete_blog(id):
    blog = Blog.query.filter_by(id=id).first()
    db.session.delete(blog)
    db.session.commit()

    return jsonify("Blog was deleted"), 200