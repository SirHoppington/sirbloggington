from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileRequired, FileAllowed
from werkzeug.utils import secure_filename

class AddBlog(FlaskForm):
    """Add new blog form."""
    title = StringField(
        'Title',
        [DataRequired()],
        id='title'
    )
    summary = TextAreaField(
        'Summary',
        [DataRequired()],
        id='summary'
    )
    contentcode = TextAreaField(
        'Content',
        id='contentcode'
    )
    feature_image = FileField(validators=[FileRequired(), FileAllowed(['jpg', 'png'], 'Images only!')], id='image')
    thumbnail = FileField('Thumbnail (200x250)', validators=[FileRequired(), FileAllowed(['jpg', 'png'], 'Images only!')], id='thumbnail')
