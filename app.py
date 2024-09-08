import dotenv
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_jwt_extended import JWTManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    tasks = db.relationship('Task', backref='owner', lazy=True)

    def __init__(self, email, password):
        self.email = email
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rotas
@app.route('/')
@login_required
def index():
    return redirect(url_for('tasks'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('tasks'))
        flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords must match')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            flash('Task content is required')
            return redirect(url_for('tasks'))

        new_task = Task(content=content, owner=current_user)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('tasks'))

    user_tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks.html', tasks=user_tasks)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/delete/<int:id>')
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.owner != current_user:
        flash('You cannot delete this task.')
        return redirect(url_for('tasks'))

    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('tasks'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
