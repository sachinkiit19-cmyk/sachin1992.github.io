from flask import Flask, render_template, request, redirect, session, flash,url_for
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
import random
import os
import uuid
import sqlite3

# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------- USER TABLE ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

with app.app_context():
    db.create_all()

# ---------------- MAIL ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sachin.kiit19@gmail.com'
app.config['MAIL_PASSWORD'] = 'vhrpbisrfwqnjjcd'

mail = Mail(app)

# ---------------- UPLOAD ----------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DOCUMENT_NAMES = {
    "coi": "Certificate of Incorporation",
    "moa": "Memorandum of Association",
    "aoa": "Articles of Association",
    "gst": "GST Certificate",
    "pan": "Company PAN",
    "cheque": "Cancelled Cheque",

    "d1_pan": "Director 1 PAN",
    "d1_aadhar": "Director 1 Aadhar",
    "d1_dl": "Director 1 Driving License",
    "d1_voter": "Director 1 Voter ID",
    "d1_photo": "Director 1 Photo"
}

# Required documents
REQUIRED_DOCS = ['aadhaar', 'pan', 'photo']

# ---------------- HOME (OTP) ----------------
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        email = request.form.get('email')
        otp = str(random.randint(100000, 999999))

        session['otp'] = otp
        session['email'] = email

        msg = Message('OTP', sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f"Your OTP is {otp}"
        mail.send(msg)

        return redirect('/verify')

    return render_template('home.html')

# ---------------- VERIFY ----------------
@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        if request.form.get('otp') == session.get('otp'):
            return redirect('/signup')
        else:
            flash("Invalid OTP")

    return render_template('verify.html')

# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = User(
            name=request.form.get('name'),
            email=session.get('email'),   # use verified email
            password=request.form.get('password')
        )
        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('signup.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(
            email=request.form.get('email'),
            password=request.form.get('password')
        ).first()

        if user:
            session['user'] = user.email
            return redirect('/register')
        else:
            flash("Invalid login")

    return render_template('login.html')

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        business_name = request.form.get('business_name')
        business_type = request.form.get('business_type')
        industry = request.form.get('industry')

        owner_name = request.form.get('owner_name')
        mobile = request.form.get('mobile')
        email = request.form.get('email')

        # 👉 Save to database here (optional for now)
        print("Registered:", owner_name, mobile, email)

        # 🔥 Redirect to upload page
        return redirect(url_for('upload'))

    return render_template('register.html')   # your current HTML file


# ---------------- UPLOAD (GET + POST MERGED) ----------------
REQUIRED_DOCS = list(DOCUMENT_NAMES.keys())

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        folder = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()))
        os.makedirs(folder, exist_ok=True)

        uploaded_docs = []
        missing_docs = []

        for doc in REQUIRED_DOCS:
            file = request.files.get(doc)

            if file and file.filename != '':
                filename = f"{doc}_{file.filename}"
                file.save(os.path.join(folder, filename))
                uploaded_docs.append(DOCUMENT_NAMES[doc])
            else:
                missing_docs.append(DOCUMENT_NAMES[doc])

        session['uploaded_docs'] = uploaded_docs
        session['missing_docs'] = missing_docs

        return redirect('/status')

    return render_template('upload.html')
# ---------------- STATUS PAGE ----------------
@app.route('/status')
def status():
    return render_template(
        'status.html',
        uploaded=session.get('uploaded_docs', []),
        missing=session.get('missing_docs', [])
    )

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)