from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
import math
from flask_mail import Mail
from werkzeug.utils import secure_filename

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail_password']

)
mail = Mail(app)
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    '''
    sno name email phone_no msg date
    '''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(12), nullable=False)
    phone_no = db.Column(db.String(120), unique=True, nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12))


class Posts(db.Model):
    '''
    sno name email phone_no msg date
    '''
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=False, nullable=False)
    content = db.Column(db.String(120), nullable=False)
    img_file = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(12))
    slug = db.Column(db.String(20), nullable=False)
    tag_line = db.Column(db.String(50), nullable=False)
    # date = db.Column(db.String(12))


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()#[0:params['no_of_posts']]
    last = math.ceil(len(posts) / int(params['no_of_posts']))
    # pagination logic
    # first
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)

    posts = posts[(page - 1) * (params['no_of_posts']):(page - 1) * (params['no_of_posts']) + (params['no_of_posts'])]

    if page == 1:
        previous = "#"
        next = "/?page=" + str(page + 1)

    elif (page == last):
        previous = "/?page=" + str(page - 1)
        next = "#"

    else:
        previous = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts, previous=previous, next=next)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


@app.route("/about")
def about():
    return render_template('about.html', params=params)


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno == '0':
                post = Posts(title=box_title, slug=slug, content=content, img_file=img_file, tag_line=tline, date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tag_line = tline
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/' + sno)

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post)


@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):

        if request.method == 'POST':
            f = request.files['file1']
            f.save(secure_filename(f.filename))
            return "Uploaded Successfully"


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()

        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == 'POST':
        #     redirect to admin panel
        username = request.form.get('uname')
        userPass = request.form.get('Pass')
        if (username == params['admin_user'] and userPass == params['admin_password']):
            #         set session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)

    else:
        return render_template('sign-in.html', params=params)

    return render_template('sign-in.html', params=params)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
        # add entry to the database
        name = request.form.get('name')
        email = request.form.get('email')
        msg = request.form.get('message')
        phone = request.form.get('phone')

        '''
        sno name email phone_no msg date
        '''

        entry = Contacts(name=name, email=email, phone_no=phone, msg=msg, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('new message from' + name, sender=email,
                          recipients=[params['gmail_user']],
                          body=msg + "\n" + phone)

    return render_template('contact.html', params=params)


@app.route("/post")
def post():
    return render_template('post.html', params=params)


if __name__ == '__main__':
    app.run(debug=True)

# app.run(debug=True)
