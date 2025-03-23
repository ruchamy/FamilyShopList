from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pandas as pd
import os

DATA_DIR = "shopping_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///purchasesDB.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)


with app.app_context():
    db.create_all()


class Purchase:
    def __init__(self, product_name: str, category: str, quantity: int, price: float, date: str = None):
        self.product_name = product_name
        self.category = category
        self.quantity = quantity
        self.price = price
        self.date = date if date else datetime.now().strftime("%Y-%m-%d")  # תאריך ברירת מחדל להיום


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


@app.route('/shopping/<user_email>', methods=['GET', 'POST'])
def shopping(user_email):
    file_path = os.path.join(DATA_DIR, f"{user_email}.csv")
    if request.method == 'POST':
        new_purchase = pd.DataFrame([{
            "product": request.form['product'],
            "category": request.form['category'],
            "quantity": request.form['quantity'],
            "price": request.form['price'],
            "date": request.form['date']
        }])
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df = pd.concat([df, new_purchase], ignore_index=True)
        else:
            df = new_purchase
        df.to_csv(file_path, index=False)
    return redirect(url_for('view_purchases', user_email=user_email))


@app.route("/view_purchases/<user_email>")
def view_purchases(user_email):
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

    file_path = os.path.join(DATA_DIR, f"{user_email}.csv")
    purchases = []
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        df["date"] = df["date"].dt.date
        if start_date and end_date:
            mask = (df["date"] >= start_date) & (df["date"] <= end_date)
        else:
            mask = (df["date"] >= datetime.now().date() - timedelta(days=7))
        df = df[mask]
        purchases = df.to_dict(orient="records")
    return render_template('shopping.html', user_email=user_email,purchases=purchases)


if __name__ == '__main__':
    app.run(debug=True)
