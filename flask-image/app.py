import sys

from flask import Flask, request, jsonify, flash, render_template, url_for
from flask_bootstrap import Bootstrap
from flask_flatpages import FlatPages
#db = SQLAlchemy()

app = Flask(__name__)

#POSTGRES = {
#    'user':'dbuser',
#    'pw':'H0pN3TS3cUR3P@SSW0rd',
#    'db':'blogdb',
#    'host':'localhost',
#    'port':'5432',
#}
#app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
#app.config['DEBUG']
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://dbuser:H0pN3TS3cUR3P@SSW0rd@localhost/my_database'

#db.init_app(app)

# Blueprints for auth routes
from auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

# Blueprints for non-auth rotues
from main import main as main_blueprint
app.register_blueprint(main_blueprint)

# this is a comment that has been edited thrice!

if __name__=='__main__':
        app.run(debug=True, host='0.0.0.0')

