from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask_ckeditor import CKEditorField


class CreatePost(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    image = FileField("Select a picture", validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'],
                                                                  'Only images are allowed!')])
    body = CKEditorField("Post content", validators=[DataRequired()])
    submit = SubmitField("Submit post", render_kw={"class": "my-custom-class"})

    def validate_file(self, field):
        file = field.data
        if file:
            if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                raise ValidationError('Invalid file format. Please upload an image.')

    def validate_body(self, field):
        if not field.data.strip():
            raise ValidationError('Post content is required.')


class ContactUs(FlaskForm):
    name = StringField("Your name", validators=[DataRequired()])
    email = StringField("Email address", validators=[DataRequired(), Email()])
    phone = StringField("Phone number", validators=[DataRequired()])
    message = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Send")


class Register(FlaskForm):
    name = StringField("Your name", validators=[DataRequired()])
    email = StringField("Email address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(),
                                                     EqualTo("confirm_pass", message='Passwords must match')])
    confirm_pass = PasswordField("Confirm Password", validators=[DataRequired(),
                                                                 EqualTo("password", message='Passwords must match')])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class Profile(FlaskForm):
    image = FileField("Select image", validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'],
                                                              'Only images are allowed!')])
    name = StringField("Your name", validators=[DataRequired()])
    email = StringField("Email address", validators=[DataRequired(), Email()])
    save = SubmitField("Save changes")

    def validate_file(self, field):
        file = field.data
        if file:
            if file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                pass
            else:
                raise ValidationError('Invalid file format. Please upload an image.')
