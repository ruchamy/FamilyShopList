from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasksDB.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            return redirect(url_for('shopping', user_email=email))
        else:
            return render_template('message.html', message="האימייל או הסיסמה שגויים", url="/", url_text="להתחברות שוב")
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            return render_template('message.html', message="האימייל כבר קיים", url="/login", url_text="התחבר")
        new_ser = User(email=email, password=password)
        db.session.add(new_ser)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/shopping/<user_email>')
def shopping(user_email):
    return render_template('shopping.html', user_email=user_email)


if __name__ == '__main__':
    app.run(debug=True)
