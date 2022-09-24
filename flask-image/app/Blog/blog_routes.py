import os
from flask import Blueprint, request, jsonify, make_response, render_template, render_template_string, url_for, redirect, json
from flask_login import login_required, current_user
from app import db
from flask_jwt_extended import jwt_required
from app.Blog.blog_model import Blog
from app.Tag.tag_model import Tag
from app.Tags_Blog.tag_blog_table import tag_blog
from app.forms import AddBlog
from werkzeug.utils import secure_filename
from datetime import datetime
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
                file = request.files['file']
                filename = secure_filename(file.filename)
                file.save(os.path.join('static/imgs', filename))
                tags = request.form.getlist('tags[]')
                new_blog = Blog(title=form.title.data, content=form.contentcode.data, feature_image=filename)
                db.session.add(new_blog)
                for tag in tags:
                    tag_exists = db.session.query(Tag.name, Tag.id).filter(
                        Tag.name == tag).first()
                    if tag_exists:
                        new_blog.tags.append(tag_exists)
                        db.session.commit()
                    else:
                        new_tag = Tag(name=tag)
                        new_blog.tags.append(new_tag)
                        db.session.add(new_tag)
                        db.session.commit()
                db.session.commit()
                id = db.session.query(Blog.id).filter(
                    Blog.title == form.title.data).first()
                idInt = str(id).replace('(','').replace(',','').replace(')','')
                #message = "Great success new post saved with ID: {}".format(id)
                #resp = jsonify({'message': message})
                #return resp
                return "Great success new post saved with ID: {}".format(idInt)
            except Exception as e:
                return(str(e))
    elif request.is_json:
        alltags = request.get_json()
        taglist = [tag for tag in alltags['values']]
        #return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    return render_template("add_blog.html",
                           form=form, blogs=latest[:4])

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
    return render_template("test_blog.html",
                       form=form, blogs=latest[:10])

@blogs.route('/blogs', methods=["GET"])
def get_all_blogs():
    blogs = Blog.query.all()
    latest = sorted(blogs, reverse=True, key=lambda b: b.created_at)
    if len(latest) == 0:
        return "No Blogs posted."
    elif len(latest) < 2:
        return render_template('index.html', blogs=latest, homepage=latest, featured=latest[0])
    elif len(latest) < 4:
        return render_template('index.html', blogs=latest, homepage=latest[0:2], featured=latest[0])
    else:
        return render_template('index.html', blogs=latest[:4], homepage=latest[0:2], featured=latest[0])
#    serialized_data = []
#    for blog in blogs:
#        serialized_data.append(blog.serialize)

#    return jsonify({"all_blogs": serialized_data})

@blogs.route('/blog/<int:id>', methods=["GET"])
def get_single_blog(id):
    blogs = Blog.query.all()
    latest = sorted(blogs, reverse=True, key=lambda b: b.created_at)
    blog = db.session.query(Blog.title, Blog.content, Blog.feature_image, Blog.created_at,Tag.name).filter(Blog.id==id).first()
    html = my_renderer(blog.content)
    query_tags = db.session.query(Tag.name).filter((tag_blog.c.blog_id==id) & (tag_blog.c.tag_id==Tag.id)).all()
    #query_tags = Blog.query.join(tag_blog).join(Tag).filter((tag_blog.c.blog_id==id) & (tag_blog.c.tag_id==Tag.id)).all()
    tags = db.session.query(Tag.name).filter(Blog.id==id).all()
    #postTags = db.session.query(Tag.name).filter(Tag.id == tag_blog.tag_id).filter(tag_blog.blog_id == Blog.id).all()
    middle_index = len(query_tags)//2
    return render_template('blog_post.html', blog=blog, blogs=latest[:4], html=html, query_tags=query_tags, first_half_tags=query_tags[:middle_index], second_half_tags=query_tags[middle_index:])
   # serialized_blog = blog.serialize
  #  serialized_blog["tags"] = []

   # for tag in blog.tags:
   #     serialized_blog["tags"].append(tag.serialize)

    #    return jsonify({"single_blog": serialized_blog})

@blogs.route('/blog/<tag>', methods=["GET"])
def get_tags(tag):
    blogs = Blog.query.all()
    latest = sorted(blogs, reverse=True, key=lambda b: b.created_at)
    tag = db.session.query(Tag.name, Tag.id).filter(
        Tag.name == tag).first()
    query_blogs = db.session.query(Blog.title, Blog.created_at, Blog.id).filter(
        (tag_blog.c.blog_id == Blog.id) & (tag_blog.c.tag_id == Tag.id)).filter(Tag.name == tag.name).all()
    return render_template('tag_categories.html', tag=tag, blogs=latest[:4],query_blogs=query_blogs)

@blogs.route('/update_blog/<int:id>', methods=["POST", "GET"])
@login_required
def update_blog(id):
    blogs = Blog.query.all()
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
        return render_template("update_blog.html", form=form, blogs=latest[:4], id=blog.id, blog=blog, query_tags=query_tags)

@blogs.route('/delete_blog/<int:id>', methods=["DELETE"])
@login_required
def delete_blog(id):
    blog = Blog.query.filter_by(id=id).first()
    db.session.delete(blog)
    db.session.commit()

    return jsonify("Blog was deleted"), 200