from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from flask_ckeditor import CKEditorField
import re


class CreatePost(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(5, 250)])
    subtitle = StringField("Subtitle", validators=[DataRequired(), Length(10, 250)])
    image = FileField("Select a picture", validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'],
                                                                  'Only images are allowed!')])
    body = CKEditorField("Post content", validators=[DataRequired(), Length(250, 5000)])
    submit = SubmitField("Submit post", render_kw={"class": "my-custom-class"})

    def validate_file(self, field):
        file = field.data
        if file:
            if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                raise ValidationError('Invalid file format. Please upload an image.')


class ContactUs(FlaskForm):
    name = StringField("Your name", validators=[DataRequired()])
    email = StringField("Email address", validators=[DataRequired(), Email()])
    phone = StringField("Phone number", validators=[DataRequired()])
    message = TextAreaField("Message", validators=[DataRequired(), Length(min=50)])
    submit = SubmitField("Send")


class Register(FlaskForm):
    name = StringField("Your name", validators=[DataRequired(), Length(4, 100)])
    email = StringField("Email address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(8, 30),
                                                     EqualTo("confirm_pass", message='Passwords must match')])
    confirm_pass = PasswordField("Confirm Password", validators=[DataRequired(),
                                                                 EqualTo("password", message='Passwords must match')])
    submit = SubmitField("Register")

    def validate_password(self, field):
        password = field.data
        reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{6,30}$"
        # compiling regex
        pat = re.compile(reg)
        # searching regex
        mat = re.search(pat, password)
        # validating conditions
        if not mat:
            raise ValidationError("The password must contain at least one upper-, one lowercase character, one number "
                                  "and one of the following special characters @$!%*#?&")


class LoginForm(FlaskForm):
    email = StringField("Email address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class Profile(FlaskForm):
    image = FileField("Select image", validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'],
                                                              'Only images are allowed!')])
    name = StringField("Your name", validators=[DataRequired(), Length(4, 100)])
    email = StringField("Email address", validators=[DataRequired(), Email()])
    save = SubmitField("Save changes")

    def validate_file(self, field):
        file = field.data
        if file:
            if file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                pass
            else:
                raise ValidationError('Invalid file format. Please upload an image.')
