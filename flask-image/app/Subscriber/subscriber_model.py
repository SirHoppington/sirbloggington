from app import db


class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)

    @property
    def serialize(self):
        return {
            'id' : self.id,
            'name' : self.name,
            'email' : self.email
        }

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return '<email {}>'.format(self.email)