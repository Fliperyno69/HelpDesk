from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
# proc to do pici nefunguje kdyz je to stahly? ↑
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # NEMAZAT!

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///helpdesk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# TODO: oddkomentovat az bude ready smpt

app.config['MAIL_SERVER'] = '#'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '#'
app.config['MAIL_PASSWORD'] = '#'

# TODO: fix mailing
mail = Mail(app)

db = SQLAlchemy(app)

ADMIN_EMAILS = [
    'admin.admin@omnipol.cz',
    # sem nahazim dalsi adminy
]


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('tickets', lazy=True))
    status = db.Column(db.String(50), default='Open')
    priority = db.Column(db.String(50), default='Normal')
    response = db.Column(db.Text, nullable=True)


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin_key = request.form.get('admin_key', '')

        if not username.endswith('@omnipol.cz'):
            flash('Registration is only allowed for @omnipol.cz email addresses.')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.')
            return redirect(url_for('register'))

        is_admin = username in ADMIN_EMAILS
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, is_admin=is_admin)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # Corrected this line
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        print(f"User found: {user}")
        if user and check_password_hash(user.password, password):
            session['username'] = user.username

            if user.username in ADMIN_EMAILS:
                user.is_admin = True
                db.session.commit()

            session['is_admin'] = user.is_admin
            print(f"Login successful for user: {user.username}")
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')
            print(f"Invalid login attempt for user: {username}")

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('You need to login first!')
        return redirect(url_for('login'))
    return render_template('dashboard.html')


@app.route('/submit_ticket', methods=['GET', 'POST'])
def submit_ticket():
    if 'username' not in session:
        flash('You need to login first!')
        return redirect(url_for('login'))

    if request.method == 'POST':  # Corrected this line
        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        user = User.query.filter_by(username=session['username']).first()
        print(f"User for ticket: {user}")

        if user is None:
            flash('User not found. Please log in again.')
            return redirect(url_for('login'))

        new_ticket = Ticket(title=title, description=description, priority=priority, user=user)
        db.session.add(new_ticket)
        db.session.commit()

        flash('Ticket submitted successfully!')
        return redirect(url_for('dashboard'))

    return render_template('submit_ticket.html')


@app.route('/tickets')
def list_tickets():
    if 'username' not in session:
        flash('You need to login first!')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    tickets = Ticket.query.filter_by(user_id=user.id).all() if not user.is_admin else Ticket.query.all()
    return render_template('tickets.html', tickets=tickets)


@app.route('/admin/dashboard')
def admin_dashboard():
    if 'username' not in session or not session['is_admin']:
        flash('Admin access required.')
        return redirect(url_for('login'))
    users = User.query.all()
    tickets = Ticket.query.all()
    return render_template('admin_dashboard.html', users=users, tickets=tickets)


@app.route('/set_admin/<username>', methods=['POST'])
def set_admin(username):
    if 'username' not in session or not session['is_admin']:
        flash('Admin access required.')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=username).first()
    if user:
        user.is_admin = True
        db.session.commit()
        flash('User elevated to admin successfully.')
    else:
        flash('Failed to update user status.')
    return redirect(url_for('admin_dashboard'))


@app.route('/respond_ticket/<int:ticket_id>', methods=['POST'])
def respond_ticket(ticket_id):
    if 'username' not in session or not session['is_admin']:
        flash('Admin access required.')
        return redirect(url_for('login'))

    response = request.form['response']
    ticket = Ticket.query.get(ticket_id)

    if ticket:
        ticket.response = response
        ticket.status = 'Responded'
        db.session.commit()

        # TODO: zase zasranej fix

        user = User.query.get(ticket.user_id)
        msg = Message('Your Ticket Has Been Responded',
                      sender='your-email@example.com',
                      recipients=[user.username])
        msg.body = f"Hello {user.username},\n\nYour ticket titled '{ticket.title}' has been responded to. Here is the response:\n\n{response}\n\nBest regards,\nHelpDesk Team"
        mail.send(msg)

        flash('Response sent successfully and email notification sent to the user.')
    else:
        flash('Ticket not found.')

    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    app.run(debug=True)

# snad to bude funngovat bismillah
