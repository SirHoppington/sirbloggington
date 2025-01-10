import click
from flask import Flask, redirect, request, render_template
from flask_admin import Admin as FlaskAdmin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask.cli import with_appcontext
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config, default_admin, admin_password, default_firstname, default_lastname
from werkzeug.security import generate_password_hash
from flask_simplemde import SimpleMDE
from flask_login import LoginManager
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
flask_admin = FlaskAdmin()

def create_app(config_name=None):
    if config_name is None:
        app = Flask(__name__, instance_path='/usr/var/src/app')
        app.config.from_object(config.get('development'))
    else:
        app = Flask(__name__, instance_path='/usr/var/src/app')
        app.config.from_object(config.get(config_name))
    db.init_app(app)
    migrate.init_app(app,db)
    CORS(app)
    SimpleMDE(app)
    mail.init_app(app)
    flask_admin.init_app(app)
    login_manager.login_view='login.log_in'
    login_manager.init_app(app)

    @app.before_first_request
    def create_admin():
        db.create_all()
        # if this returns a user, then the email already exists in database
        if not User.query.filter_by(email=default_admin).first():
            # Generate default admin user account:
            new_user = User(
                email=default_admin,
                password=generate_password_hash(
                    admin_password, method='sha256'),
                firstname=default_firstname,
                lastname=default_lastname,
                role="admin")

            # add the new user to the database
            db.session.add(new_user)
            db.session.commit()
        return True

    from app.Blog.blog_routes import blogs
    app.register_blueprint(blogs)

    from app.User.user_route import user_route
    app.register_blueprint(user_route)

    from app.Admin.admin_route import github
    app.register_blueprint(github)

    from app.User.user_model import User
    from app.Blog.blog_model import Blog
    from app.Tag.tag_model import Tag
    from app.Subscriber.subscriber_model import Subscriber

    from app.Login.login_route import login
    app.register_blueprint(login)
    from app.Admin.admin_route import SecureModelView, MessageAdmin

    flask_admin.add_view(SecureModelView(User, db.session))
    flask_admin.add_view(MessageAdmin(Blog, db.session))
    flask_admin.add_view(SecureModelView(Subscriber, db.session))
    flask_admin.add_view(SecureModelView(Tag, db.session))

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized_handler():
        return redirect('/login?next=' + request.path)
    return app
