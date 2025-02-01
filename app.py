from flask import Flask, jsonify, request, session, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_session import Session
import secrets
from datetime import timedelta, datetime
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app, supports_credentials=True)
bcrypt = Bcrypt(app)
# Configure database URI for Heroku PostgreSQL
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri or "sqlite:///forum.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure file uploads
UPLOAD_FOLDER = os.path.join("static", "images", "uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure sessions and secret key
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex())
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
app.permanent_session_lifetime = timedelta(days=7)

# Initialize extensions
db = SQLAlchemy(app)
Session(app)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    profile_picture = db.Column(db.String(300), nullable=False, default='/static/images/album.webp')
    site_url = db.Column(db.String(120), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "site_url": self.site_url
        }

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow)
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

with app.app_context():
    if not db.engine.has_table("User") and not db.engine.has_table('Blog'):  # Check if 'user' table exists
        db.create_all()

# Routes
@app.route("/")
def home():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/profile", methods=["GET"])
def index():
    try:
        if session['username']:
            user = User.query.filter_by(username=session["username"]).first()
            blogs = Blog.query.filter_by(username=session["username"])
            return render_template("index.html", 
                                message=user.username,
                                site_url=user.site_url,
                                image=user.profile_picture,
                                posts=blogs)
    except:
        return render_template("signin.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            session["username"] = username
            session.permanent = True
            return redirect("/profile")
        return render_template("signin.html", message="Invalid credentials")
    return render_template("signin.html")

@app.route("/create_user", methods=["POST", "GET"])
def create_user():
    if request.method == "GET":
        return render_template("register.html")
    
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    site_url = request.form["site_url"]
    password = bcrypt.generate_password_hash(password).decode('utf-8')      # NOTE: Password is hashed here
    # Check for existing username
    if User.query.filter_by(username=username).first():
        return render_template("register.html", message="Username already taken")

    # Check for existing email
    if User.query.filter_by(email=email).first():
        return render_template("register.html", message="Email already registered")

    try:
        new_user = User(
            username=username,
            email=email,
            password=password,  # NOTE: You should hash passwords in production!
            site_url=site_url
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    
    except Exception as e:
        db.session.rollback()  # Important to prevent locked database
        return render_template("register.html", message="Error creating user")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/settings", methods=["POST"])
def settings():
    if "username" not in session:
        return redirect(url_for("login"))
    
    user = User.query.filter_by(username=session["username"]).first()
    file = request.files.get("pfp")
    site_url = request.form.get("site_url")
    
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        user.profile_picture = f"/static/images/uploads/{filename}"
    
    if site_url:
        user.site_url = site_url
    
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/feed")
def show_feed():
    blogs = Blog.query.order_by(Blog.timestamp.desc()).all()
    return render_template("feed.html", blogs=blogs)

@app.route("/makepost", methods=["POST"])
def make_post():
    if "username" not in session:
        return redirect(url_for("login"))
    
    user = User.query.filter_by(username=session["username"]).first()
    new_post = Blog(
        title=request.form["blog_title"],
        content=request.form["blog_content"],
        user=user
    )
    db.session.add(new_post)
    db.session.commit()
    return redirect(url_for("index"))

# API Endpoints
@app.route("/user/<username>", methods=["GET"])
def user_lookup(username):
    user = User.query.filter_by(username=username).first()
    blogs = Blog.query.filter_by(username=username)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "user": user.to_dict(),
        "blogs": [blog.to_dict() for blog in blogs]
    })

@app.route("/users", methods=["GET"])
def total_users():
    users = User.query.all()
    return jsonify([{
        "username": user.username,
        "site_url": user.site_url,
        "pfp": f"{request.host_url[:-1]}{user.profile_picture}"
    } for user in users])

@app.route("/delete/<int:post_id>", methods=["GET"])
def delete_post(post_id):
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    post = Blog.query.get_or_404(post_id)
    if post.username != session["username"]:
        return jsonify({"error": "Forbidden"}), 403
    
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=False)