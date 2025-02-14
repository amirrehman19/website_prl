import smtplib
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, abort,session

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
from datetime import date

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''
GMAIL_USER="amirrehman16022022@gmail.com"
GMAIL_PASSWORD="tvim qvva qbys fbxy"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CONFIGURE TABLE
class BlogPost(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()





# WTForm
class CreatePostForm(FlaskForm):
    title = StringField(" Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    # img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    img_url = StringField("Post Image URL")

    body = CKEditorField("Post Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True  # Store admin status in session
            return redirect(url_for("get_all_posts"))
        else:
            return "<h1>Invalid credentials. Try again.</h1>"
    return render_template("admin_login.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)  # Remove admin status from session
    return redirect(url_for("get_all_posts"))
def admin_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return abort(403)  # Forbidden
        return func(*args, **kwargs)
    return wrapper




@app.route("/submit_contact", methods=["POST"])
def submit_contact():
    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]
    message = request.form["message"]
    subject="NEW SUBMISSION OF A CLIENT"
    email_body=(
        f"Name: {name}"
        f"email: {email}"
        f"phone: {phone}"
        f"message:{message}"
    )
    with smtplib.SMTP("smtp.gmail.com",587) as server:
        server.starttls()
        server.login(GMAIL_USER,GMAIL_PASSWORD)
        server.sendmail(from_addr=GMAIL_USER,to_addrs=GMAIL_USER,msg=
                        f"subject: {subject}\n\n{email_body}")

    confirmation="<h1>YOUR MESSAGE HAS BEEN SENT SUCCESSFULLY</h1>"



    return (
        confirmation +
        f"<h1>Thank you, {name}!</h1>"
        f"<p>Email: {email}</p>"
        f"<p>Phone: {phone}</p>"
        f"<p>Message: {message}</p>"
    )

@app.route("/about")
def about():
    return render_template("about.html")

@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("about.html", all_posts=posts,is_admin=session.get("admin"))


@app.route("/post/<int:post_id>")
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    return render_template("post.html", post=requested_post)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=form.author.data,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        try:
            db.session.add(new_post)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Error:", e)
        finally:
            db.session.close()

        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    from waitress import serve
    serve(app, port=5002)
