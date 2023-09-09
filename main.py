from functools import wraps
import cloudinary
from flask import Flask, render_template, redirect, url_for, request, abort
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import datetime
import smtplib
import os
import forms
from sqlalchemy.orm import relationship
from cloudinary import uploader

cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ["CLOUD_API"],
    api_secret=os.environ["API_SECRET"]
)


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

ckeditor = CKEditor()
ckeditor.init_app(app)

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
Bootstrap5(app)

# CONNECT TO DB
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URI"), "sqlite:///posts.db"
db = SQLAlchemy()
db.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


def admin_only(function):
    @wraps(function)
    def wrapper_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            abort(403)
        return function(*args, **kwargs)
    return wrapper_function


def admin_or_author(function, comment):
    @wraps(function)
    def wrapper_function(*args, **kwargs):
        if not current_user.id != comment.author_id or current_user.id != 1:
            abort(403)
        return function(*args, **kwargs)
    return wrapper_function


def send_email(name, email_address, phone, message):
    with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
        connection.starttls()
        connection.login(os.environ["MY_EMAIL"], os.environ["PW"])
        connection.sendmail(from_addr=email_address, to_addrs=os.environ["MY_EMAIL"],
                            msg=f"Subject:{name} wants to contact you\n\nYou've got this message: {message}\n"
                                f"Sent from {email_address}\nPhone: {phone}")


def upload_image():
    uploaded_file = request.files["image"]
    if uploaded_file.filename != "":
        result = cloudinary.uploader.upload(uploaded_file)
        image_url = result["secure_url"]
        return image_url


# CONFIGURE TABLE
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250))
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # Define one-to-many relationship with comments
    comments = relationship("Comment", backref="blog_post", lazy=True)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    img_url = db.Column(db.String(250))
    bio = relationship("UserBio", backref="user", uselist=False)
    # Define one-to-many relationships
    posts = relationship("BlogPost", backref="author", lazy=True)
    comments = relationship("Comment", backref="author", lazy=True)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(100), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("blog_post.id"), nullable=False)


class UserBio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    genre = db.Column(db.String(250))
    about = db.Column(db.String(2000))
    profession = db.Column(db.String(250))
    linkedin = db.Column(db.String(250))
    twitter = db.Column(db.String(250))
    facebook = db.Column(db.String(250))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    num = 3
    all_posts = BlogPost.query.order_by(BlogPost.id.desc()).all()
    return render_template("index.html", posts=all_posts, num=num)


@app.route('/more-posts<int:num>')
def show_more(num):
    num += 3
    all_posts = BlogPost.query.order_by(BlogPost.id.desc()).all()
    return render_template("index.html", posts=all_posts, num=num)


@app.route('/post/<int:post_id>')
def get_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comments = Comment.query.filter_by(post_id=post_id).all()
    return render_template("post.html", post=requested_post, comments=comments)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["POST", "GET"])
def contact():
    contact_form = forms.ContactUs()
    success_message = None
    if contact_form.validate_on_submit():
        name = contact_form.name.data
        email_address = contact_form.email.data
        phone = contact_form.phone.data
        message = contact_form.message.data
        send_email(name, email_address, phone, message)
        success_message = "Your message has been successfully sent."
        return render_template("contact.html", success_message=success_message)
    return render_template("contact.html", form=contact_form, success_message=success_message)


@app.route("/add", methods=["GET", "POST"])
@login_required
@admin_only
def add_post():
    form = forms.CreatePost()
    date = datetime.datetime.now().date().strftime("%B %d, %Y")
    if request.method == "POST":
        form.validate_file(form.image)
        new_post = BlogPost(title=form.title.data, subtitle=form.subtitle.data, date=date,
                            author_id=current_user.id, body=form.body.data)
        image = upload_image()
        if image:
            new_post.img_url = image
        else:
            new_post.img_url = "https://res.cloudinary.com/dw6opo6zj/image/upload/v1694187951/xucfh3zxpl81q9y2f6cf.png"
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("create-post.html", form=form)


@app.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = forms.CreatePost(title=post.title, subtitle=post.subtitle, img_url=post.img_url, body=post.body)
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.body = edit_form.body.data
        edit_form.validate_file(edit_form.image)
        image = upload_image()
        if image:
            post.img_url = image
        else:
            post.img_url = post.img_url
        db.session.commit()
        return redirect(url_for("get_post", post_id=post.id))
    return render_template("create-post.html", form=edit_form, is_edit=True)


@app.route("/delete/<int:post_id>")
@login_required
@admin_only
def delete(post_id):
    post = db.get_or_404(BlogPost, post_id)
    comments = Comment.query.filter_by(post_id=post_id).all()
    for comment in comments:
        db.session.delete(comment)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/login", methods=["GET", "POST"])
def login():
    login_form = forms.LoginForm()
    error = None
    if login_form.validate_on_submit():
        user_email = login_form.email.data
        user = User.query.filter_by(email=user_email).scalar()
        if user:
            password = check_password_hash(user.password, login_form.password.data)
            if password:
                login_user(user)
                return redirect(url_for("home"))
            else:
                error = "The username and password doesn't match."
        else:
            error = "This email address is not registered."
    return render_template("login.html", form=login_form, error=error)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"])
def register():
    registration_form = forms.Register()
    if registration_form.validate_on_submit():
        new_user = User()
        new_user.name = registration_form.name.data
        new_user.email = registration_form.email.data
        new_user.password = generate_password_hash(registration_form.password.data, method="pbkdf2", salt_length=16)
        new_user.img_url = "https://res.cloudinary.com/dw6opo6zj/image/upload/v1694185393/qihe2lbih2oaegat3pzl.jpg"
        already_registered = User.query.filter_by(email=new_user.email).all()
        if already_registered:
            error = "This email address already exists in database, try to Log in."
            return render_template("register.html", form=registration_form, error=error)
        else:
            db.session.add(new_user)
            db.session.commit()
            login()
            return redirect(url_for("home"))
    return render_template("register.html", form=registration_form)


@app.route("/post/<int:post_id>/add_comment", methods=["GET", "POST"])
@login_required
def add_comment(post_id):
    date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    if request.method == "POST":
        new_comment = Comment(body=request.form["comment"], author_id=current_user.id,
                              post_id=post_id, date=date)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for("get_post", post_id=post_id))
    return redirect(url_for("home"))


@app.route("/my-page")
@login_required
def my_page():
    return render_template("my_page.html")


@app.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = forms.Profile(img_url=current_user.img_url, name=current_user.name, email=current_user.email)
    if form.validate_on_submit():
        user = db.get_or_404(User, current_user.id)
        form.validate_file(form.image)
        image = upload_image()
        if image:
            user.img_url = image
        user.name = form.name.data
        user.email = form.email.data
        db.session.commit()
        return redirect(url_for("my_page"))

    return render_template("my_page.html", form=form, edit_mode=True)


@app.route("/post/<int:post_id>/<int:comment_id>")
@login_required
def delete_comment(post_id, comment_id):
    comment = db.get_or_404(Comment, comment_id)
    if current_user.id == comment.author_id or current_user.id == 1:
        db.session.delete(comment)
        db.session.commit()
        return redirect(url_for("get_post", post_id=post_id))


if __name__ == "__main__":
    app.run(debug=False)
