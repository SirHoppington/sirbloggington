from flask import Blueprint, request, abort, redirect
import subprocess
from app.User.user_model import User
from app.Subscriber.subscriber_model import Subscriber
from app import db
import hmac
import hashlib
import os
from flask_admin import Admin as BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import ImageUploadField
from flask_login import current_user
from wtforms import TextAreaField
from wtforms.widgets import TextArea
from app.Blog.blog_model import Blog
from app.Tag.tag_model import Tag
from wtforms.validators import DataRequired
from flask_admin.form import Select2Widget
from wtforms import SelectMultipleField, StringField
from wtforms.validators import ValidationError
from PIL import Image
from io import BytesIO
from base64 import b64decode

github = Blueprint('github', __name__)


GITHUB_SECRET: str = os.getenv('GITHUB_SECRET', 'PLACEHOLDER')

@github.route('/github-webhook', methods=['POST'])
def webhook():
    # test update
    if request.method == 'POST':
        if not verify_signature(request):
            abort(403)
        data = request.json
        if 'ref' in data and data['ref'] == 'refs/heads/main':
            # Pull the latest code from GitHub
            subprocess.run(['git', 'pull'])
            # Rebuild and restart the Docker containers
            subprocess.run(['docker-compose', 'down'])
            subprocess.run(['docker-compose', 'up', '-d', '--build'])
            return 'Updated successfully', 200
        return 'No action taken', 200
    

def verify_signature(request):
    signature = request.headers.get('X-Hub-Signature-256')
    if signature is None:
        return False
    sha_name, signature = signature.split('=')
    if sha_name != 'sha256':
        return False

    mac = hmac.new(GITHUB_SECRET.encode(), msg=request.data, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)

class TagListField(SelectMultipleField):
    """Custom field to handle existing and new tags."""
    def pre_validate(self, form):
        """Skip validation for unknown tags to allow new ones."""
        pass

class SecureModelView(ModelView):
    def is_accessible(self):
        # Allow access only to authenticated users with admin privileges
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        # Redirect to the login page if the user is not authenticated
        return redirect('/login?next=' + request.path)
class MyView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin.html')

def render(self, template, **kwargs):
    user_email = current_user.email if current_user.is_authenticated else None
    print(f"Rendering {template} with user_email: {user_email}")
    kwargs['user_email'] = user_email
    return super(MyView, self).render(template, **kwargs)

def is_accessible(self):
    return current_user.is_authenticated

def inaccessible_callback(self, name, **kwargs):
    return redirect('/login?next=' + request.path)
        
class UserView(ModelView):
    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        from app.forms import AddBlog
        form = AddBlog()
        return self.render('admin_blog.html', form=form)

# class BlogAdmin(ModelView):
#     # Override the form field for tags
#     form_extra_fields = {
#         'tags': TagListField(
#             'Tags',
#             choices=[],  # Choices will be populated dynamically
#             widget=Select2Widget(multiple=True),
#             validators=[DataRequired()]
#         )
#     }

# def on_form_prefill(self, form, id):
#     """Prefill existing tags for the edit page."""
#     form.tags.choices = [(tag.id, tag.name) for tag in Tag.query.all()]
#     blog = Blog.query.get(id)
#     if blog:
#         form.tags.data = [tag.id for tag in blog.tags]

# def create_model(self, form):
#     """Handle tag creation during Blog creation."""
#     try:
#         tags = []
#         for tag_id in form.tags.data:
#             if tag_id.isdigit():
#                 # Existing tag
#                 tag = Tag.query.get(int(tag_id))
#             else:
#                 # New tag
#                 tag = Tag(name=tag_id)
#                 db.session.add(tag)
#             tags.append(tag)
#         blog = Blog(
#             title=form.title.data,
#             feature_image=form.feautred_image,
#             summary=form.summary.data,
#             content=form.content.data,
#             thumbnail=form.thumbnail,
#             tags=tags
#         )
#         db.session.add(blog)
#         db.session.commit()
#         return blog
#     except Exception as ex:
#         self.session.rollback()
#         raise ValidationError(f"Failed to create model: {ex}")

# def update_model(self, form, model):
#     """Handle tag creation during Blog update."""
#     try:
#         tags = []
#         for tag_id in form.tags.data:
#             if tag_id.isdigit():
#                 # Existing tag
#                 tag = Tag.query.get(int(tag_id))
#             else:
#                 # New tag
#                 tag = Tag(name=tag_id)
#                 db.session.add(tag)
#             tags.append(tag)
#         model.tags = tags
#         model.title = form.title.data
#         model.content = form.content.data
#         db.session.commit()
#         return model
#     except Exception as ex:
#         self.session.rollback()
#         raise ValidationError(f"Failed to update model: {ex}")


class SimpleMDETextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        # Add a class for targeting by SimpleMDE
        if kwargs.get('class'):
            kwargs['class'] += ' simplemde'
        else:
            kwargs.setdefault('class', 'simplemde')
        return super(SimpleMDETextAreaWidget, self).__call__(field, **kwargs)

class SimpleMDETextAreaField(TextAreaField):
    widget = SimpleMDETextAreaWidget()


UPLOAD_FOLDER = os.path.join('app/static/imgs')

class CustomUserModel(ModelView):
    # Include SimpleMDE's JavaScript and CSS
    extra_js = [
        'https://cdn.jsdelivr.net/npm/cropperjs/dist/cropper.min.js',
        'https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.js'
    ]
    extra_css = [
        'https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.css',
        'https://cdn.jsdelivr.net/npm/cropperjs/dist/cropper.min.css'
        ]

    edit_template = "admin/edit_user.html"
    create_template = "admin/add_user.html"
    # Override the form field to use SimpleMDE
    form_overrides = {
        'bio': SimpleMDETextAreaField,
        }
    
    form_extra_fields = {
        'profile_pic': ImageUploadField(
            label='Profile Picture',
            base_path=UPLOAD_FOLDER,          # Local path for file storage
            url_relative_path='/',    # Relative URL for file access
            allowed_extensions=['jpg', 'jpeg', 'png', 'gif']
        )
    }

    def on_model_change(self, form, model, is_created):
        # Handle the cropped image data
        cropped_data = form.croppedImageData.data
        if cropped_data:
            try:
                # Decode the Base64 image data
                cropped_image_data = b64decode(cropped_data.split(',')[1])  # Remove Base64 prefix
                image = Image.open(BytesIO(cropped_image_data))

                # Save the cropped image
                filename = f"{model.id}_profile_pic.png"
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                image.save(save_path)

                # Update the model's profile_pic field
                model.profile_pic = filename
            except Exception as e:
                raise ValueError(f"Error processing image: {e}")
    

class MessageAdmin(ModelView):
    # Include SimpleMDE's JavaScript and CSS
    extra_js = [
        'https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.js'
    ]
    extra_css = [
        'https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.css'
    ]

    edit_template = "admin/edit_blog.html"
    create_template = "admin/add_blog.html"
    # Override the form field to use SimpleMDE
    form_overrides = {
        'content': SimpleMDETextAreaField,
        }
    
    form_extra_fields = {
        'feature_image': ImageUploadField(
            label='Feature Image',
            base_path=UPLOAD_FOLDER,          # Local path for file storage
            url_relative_path='/',    # Relative URL for file access
            allowed_extensions=['jpg', 'jpeg', 'png', 'gif']
        ),
        'thumbnail': ImageUploadField(
            label='Thumbnail',
            base_path=UPLOAD_FOLDER,          # Local path for file storage
            url_relative_path='/imgs',    # Relative URL for file access
            allowed_extensions=['jpg', 'jpeg', 'png', 'gif']
        )
    }

    def create_form(self):
        form = super().create_form()
        form.content.data = form.content.data or ''  # Default to an empty string if no data
        return form

    def create_model(self, form):
        try:
            if form.validate():
                print("Form is valid")
            else:
                print("Form validation errors:", form.errors)
            model = super().create_model(form)
            return model
        except Exception as e:
            print("Error creating model:", e)
            raise
    
    def get_query(self):
        # Restrict queries to only show blogs created by the current user
        return super().get_query().filter(Blog.user_id == current_user.id)

    def get_count_query(self):
        # Count only blogs created by the current user
        return super().get_count_query().filter(Blog.user_id == current_user.id)

    def is_accessible(self):
        # Ensure the user is authenticated before accessing the admin panel
        return current_user.is_authenticated

    def on_model_change(self, form, model, is_created):
        # Automatically set the user_id for new blogs to the logged-in user
        if is_created:
            model.user_id = current_user.id
        else:
            # Ensure editing is only allowed for their own blogs
            if model.user_id != current_user.id:
                raise PermissionError("You can only edit your own blogs.")