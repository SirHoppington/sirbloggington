import os
from flask import Blueprint, request, jsonify, make_response, render_template, render_template_string, url_for, redirect, json, send_from_directory
from flask_login import login_required, current_user
from app import db
from app import mail
from flask_jwt_extended import jwt_required
from app.Blog.blog_model import Blog
from app.Tag.tag_model import Tag
from app.User.user_model import User
from app.Tags_Blog.tag_blog_table import tag_blog
from app.Subscriber.subscriber_model import Subscriber
from app.forms import AddBlog
from app.queries import blogs_query, subscribers_query, all_tags_query, tags_query, blogs_by_author

from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Message
import markdown
import gzip
import subprocess
from sqlalchemy.orm import joinedload

user_route = Blueprint('user_route', __name__)

@user_route.route('/profile/<id>', methods=["GET"])
def get_profile(id):

    blogs = blogs_by_author(id)
    all_tags = all_tags_query()
    tags = tags_query()
    latest = sorted(blogs, reverse=True, key=lambda b: b.created_at)
    author = db.session.query(User).filter(User.id== id).first()
    if len(latest) == 0:
        return "No Blogs posted."
    else:
        return render_template('profile.html', blogs=latest[:10],
                               tags=tags, homepage=latest[1:4], featured=latest[0], topics=all_tags[0:20], author=author)
