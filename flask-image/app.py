import click
from flask import Flask
from flask.cli import with_appcontext
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from flask_simplemde import SimpleMDE
from flask_login import LoginManager
db = SQLAlchemy()

app = Flask(__name__, instance_path='/usr/var/src/app')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
#pages = FlatPages(app)
#freezer = Freezer(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://hopnet_admin:H0pN3TADM1N@postgres/hopnet_blog'
app.config['SECRET_KEY'] = 'AAAAB3NzaC1yc2EAAAABJQAAAQEAuvjGXjjRHXzQrVWTlwkNGJ3TLkkjrX54KxvNYwk84IYVwH3OjolzssrJ8ywwpHygOVWhgA3PYR46g7pjNj3KzNiG8wrRpCc2jjCMcTyrAksdwNJMnd/UIFXpyn98fxv4Yf318BVAxwtLocP/7aqvOLORS6vOGJtOGBh+378rKF1eobpRUfGVAxmnQnArZPaLUKkDY4NJdJWVoW/y2wwVILqLIUZusRY+B3ac8BlVPypeJVonC4yEGuo7Z6iuNl2c3UtgSCNa0+VkbouLWgAux6NhvYnOYkJqM4YQ5AutDH2rRPn3l0SZLdqOUW0V66/GGT8iorhXtah+oq31OMgV9w'
app.config['SIMPLEMDE_JS_IIFE'] = True
app.config['SIMPLEMDE_USE_CDN'] = True

#app.config.update({
#    'FLATPAGES_EXTENSION' : ['.md', '.markdown'],
#    'FLATPAGES_HTML_RENDER' : my_renderer
#})
CORS(app)
db.init_app(app)
SimpleMDE(app)

login_manager = LoginManager()
login_manager.login_view = 'login.log_in'
login_manager.init_app(app)

from Blog.blog_routes import blogs
app.register_blueprint(blogs)

from User.user_model import User

from Login.login_route import login
app.register_blueprint(login)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__=='__main__':
    app.run()