from flask import Flask, jsonify, request, session, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_session import Session
import secrets
from datetime import timedelta, datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join("static","images","uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Session configuration

app.config["SESSION_PERMANENT"] = True  # Make session permanent

app.secret_key = secrets.token_hex()
app.permanent_session_lifetime = timedelta(days=7)
db = SQLAlchemy(app)


# User model for SQLAlchemy
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    profile_picture = db.Column(db.String(300), nullable=False, default='static/images/album.webp')
    site_url = db.Column(db.String(120), nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "site_url": self.site_url
        }

    def __init__(self, username, email, password, site_url):
        self.username = username
        self.email = email
        self.password = password
        self.site_url = site_url

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(), default=datetime.today())
    title = db.Column(db.String(120), nullable=True)
    content = db.Column(db.String(), nullable=True)
    username = db.Column(db.String(80), db.ForeignKey("user.username"), nullable=False)
    user = db.relationship("User", backref=db.backref('blogs', lazy=True))
    
    def to_dict(self):
        return {
            "username": self.username,
            "title": self.title,
            "date": self.timestamp.strftime('(%Y/%m/%d)'),
            "time": self.timestamp.strftime('(%H:%M)'),
            "content": self.content
        }
    
    def __init__(self, title, content, user):
        self.title = title
        self.content = content
        self.username = user.username
        self.user = user
        
        
# Initialize the database
with app.app_context():
    db.create_all()
@app.route("/")
def dashboard():
    return render_template("dashboard.html")
@app.route("/profile", methods=["GET"])
def index():
    if "username" in session:
        user_session = session["username"]
        user = User.query.filter_by(username=user_session).first()
        blogs = Blog.query.filter_by(username=user_session)
        return render_template("index.html", message=session["username"], site_url=user.site_url, image=user.profile_picture, posts=blogs)
    else:
        
        return render_template("signin.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        try:
            user = User.query.filter_by(username=username).first()
            blogs = Blog.query.filter_by(username=user.username)
            
            if user.password == password:
                session["username"] = username
                session.permanent = True
                app.logger.info(session["username"])
                user = User.query.filter_by(username=session["username"]).first()  
                return redirect("/profile")
            else:
                return render_template("signin.html",message="Wrong Username or Password")
        except:
            return render_template("signin.html", message="Error Occurred")
    else:
        return render_template("signin.html", message="Login")

@app.route("/create_user", methods=["POST", "GET"])
def create_user():
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        site_url = request.form["site_url"]
        try:
            user = User.query.filter_by(username=username).first()
            if user:
                return render_template("register.html", message="User already exists.")
            else:
                new_user = User(username=username, password=password, email=email,site_url=site_url)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for("login"))
        except:
            return render_template("register.html",message="Error Occurred")

@app.route("/logout", methods=["GET"])
def logout():
    session.pop("username",None)
    return render_template("signin.html",message="logged out")

@app.route("/dashboard",methods=["GET"])
def dash():
    
    return render_template("dashboard.html")
    
@app.route("/settings",methods=["POST"])
def settings():
    if "username" in session:
        user = User.query.filter_by(username=session["username"]).first()
        file = request.files["pfp"]
        site_url = request.form["site_url"]
        blogs = Blog.query.filter_by(username=session["username"])
        if file and not site_url:
            app.logger.info(file)
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            app.logger.info(file)
            file.save(filepath)
            user.profile_picture = "\\static\\images\\uploads\\" + filename
            db.session.commit()
            return render_template("index.html",err_msg="Change detected", image="static\\images\\uploads\\" + filename, message=user.username, site_url=user.site_url,posts=blogs)
        elif not file and site_url:
            user.site_url = site_url
            db.session.commit()
            return render_template("index.html",err_msg="Change detected", image=user.profile_picture, message=user.username, site_url=user.site_url,posts=blogs)
        else:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            user.profile_picture = "\\static\\images\\uploads\\" + filename
            user.site_url = site_url
            db.session.commit()
            return render_template("index.html",err_msg="Change detected", image="static\\images\\uploads\\" + filename, message=user.username, site_url=user.site_url,posts=blogs)
        
    else:
        return render_template("signin.html", message="Unauthorized")
        
@app.route("/feed")
def show_feed():
    try:
        blogs = Blog.query.all()
        
        return render_template("feed.html", alert="Blog Feed:", blogs=blogs)
    except:
        return render_template("feed.html", alert="No blogs have been posted")    
@app.route("/makepost", methods=["POST"])
def make_post():
    if "username" in session:
        user_session = session["username"]
        user = User.query.filter_by(username=user_session).first()
        blog_title = request.form["blog_title"]
        blog_content = request.form["blog_content"]
        new_post = Blog(blog_title,blog_content, user=user)
        users_blogs = Blog.query.filter_by(username = user_session)
        db.session.add(new_post)
        db.session.commit()
        return redirect("/profile")
    else:
        
        return render_template("signin.html")

# Start of API
@app.route("/user/<username>", methods=["GET"])
def user_lookup(username):
    user = User.query.filter_by(username=username).first()
    blogs = Blog.query.filter_by(username=username)
    new_blog = Blog("Test Blog", "This is just a test", user)
    db.session.add(new_blog)
    db.session.commit()
    if user and not blogs:
        return jsonify({
            "username": user.username,
            "email": user.email,
            "blogs": "No blogs"
        })
    elif user and blogs:
        return jsonify({
            "username": user.username,
            "email": user.email,
            "blogs": [{"time":blog.timestamp, "title": blog.title, "content": blog.content} for blog in blogs]
        })
    else:
        return jsonify({"message": "User does not exist"})

@app.route("/users", methods=["GET"])
def total_users():
    users = User.query.all()
    user_list = [{"username": user.username, "site_url": user.site_url, "pfp": "https://neko-blogs-a52478cbe33c.herokuapp.com/"+user.profile_picture} for user in users]
    
    return jsonify(user_list)    
    
@app.route("/delete/<post_id>", methods=["GET"])
def delete_post(post_id):
    post_to_delete = Blog.query.filter_by(id=post_id).first()
    user_session = session["username"]
    user = User.query.filter_by(username=user_session).first()
    users_blogs = Blog.query.filter_by(username = user_session)
    if user_session == post_to_delete.username:
        db.session.delete(post_to_delete)
        db.session.commit()
        return redirect("/profile")
    else:
        return jsonify({"message": "An error has occurred!"}) 


if __name__ == "__main__":
    app.run(debug=True)
