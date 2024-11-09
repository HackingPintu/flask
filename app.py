from flask import Flask, flash, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from models import db, User, Repository  # Import your models
import os

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip'}
CHANGE_HISTORY_FILE = 'change_history.txt'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///repos.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db.init_app(app)

with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_change_to_file(repo_id, filename, message):
    timestamp = db.func.now()
    with open(CHANGE_HISTORY_FILE, 'a') as f:
        f.write(f"{timestamp} - {message}: {filename} (repo_id: {repo_id})\n")

def read_change_history():
    if os.path.exists(CHANGE_HISTORY_FILE):
        with open(CHANGE_HISTORY_FILE, 'r') as f:
            changes = f.readlines()
        return [change.strip() for change in changes]
    return []

@app.route('/')
def landing_page():
    return render_template('landing_page.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Signup successful!', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/index')
def index():
    repos = Repository.query.all()
    return render_template('index.html', repos=repos)

@app.route('/repo/<int:repo_id>')
def repo_detail(repo_id):
    repo = Repository.query.get(repo_id)
    files = []
    repo_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(repo_id))
    if os.path.exists(repo_folder):
        for root, dirs, file_names in os.walk(repo_folder):
            for file_name in file_names:
                files.append(os.path.relpath(os.path.join(root, file_name), app.config['UPLOAD_FOLDER']))
    changes = read_change_history()
    return render_template('repo_detail.html', repo=repo, files=files, changes=changes)

@app.route('/new_repo', methods=['GET', 'POST'])
def new_repo():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            new_repo = Repository(name=name, description=description, filename=filename)
            db.session.add(new_repo)
            db.session.commit()
            return redirect(url_for('index'))
    return render_template('new_repo.html')


@app.route('/edit_file/<path:filename>', methods=['GET', 'POST'])
def edit_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if request.method == 'POST':
        content = request.form['content']
        with open(file_path, 'w') as file:
            file.write(content)
        repo_id = request.form['repo_id']
        save_change_to_file(repo_id, filename, "Edited file")
        return redirect(url_for('repo_detail', repo_id=repo_id))
    with open(file_path, 'r') as file:
        content = file.read()
    return render_template('edit_file.html', filename=filename, content=content)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete_repo/<int:repo_id>')
def delete_repo(repo_id):
    repo = Repository.query.get(repo_id)
    if repo.filename:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], repo.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    db.session.delete(repo)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
