import matplotlib

matplotlib.use('Agg')
from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pandas as pd
import os
import io
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
import numpy as np
from bs4 import BeautifulSoup
import requests
import urllib.request

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


def plot_monthly_expenses(df, img_io):
    """גרף 1: הוצאות לפי חודשים"""
    monthly_expenses = df.groupby("month")["price"].sum()
    plt.figure(figsize=(10, 5))
    plt.figure(facecolor='none')
    monthly_expenses.plot(kind="bar", color="skyblue")
    plt.title(get_display("הוצאות לפי חודשים"), horizontalalignment='right')
    plt.xlabel(get_display("חודש"), horizontalalignment='right')
    plt.ylabel(get_display("סכום ההוצאות"), horizontalalignment='right')
    plt.xticks(rotation=45)
    plt.grid(axis='y')

    plt.savefig(img_io, format="png")
    plt.close()


def plot_category_pie(df, img_io):
    """גרף 2: פילוח הוצאות לפי קטגוריות"""
    category_expenses = df.groupby("category")["price"].sum()
    labels = [get_display(label) for label in category_expenses.index]
    plt.figure(figsize=(8, 8))
    plt.figure(facecolor='none')
    plt.pie(category_expenses, labels=labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Pastel1.colors)
    plt.title(get_display("פילוח הוצאות לפי קטגוריות"))
    plt.savefig(img_io, format="png")
    plt.close()


def plot_current_vs_avg(df, img_io):
    """גרף 3: הוצאות חודש נוכחי לעומת ממוצע חודשי"""
    current_month = datetime.now().strftime('%Y-%m')
    avg_expenses = df.groupby("month")["price"].sum().mean()
    current_expenses = df[df["month"] == current_month]["price"].sum()
    plt.figure(figsize=(6, 5))
    plt.figure(facecolor='none')
    plt.bar([get_display("ממוצע"), get_display("החודש הנוכחי")], [avg_expenses, current_expenses],
            color=['gray', '#8e24aa'])
    plt.title(get_display("חודש נוכחי לעומת הוצאות חודשיות ממוצעות"))
    plt.ylabel(get_display('סה"כ הוצאות'))
    plt.savefig(img_io, format="png")
    plt.close()


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
    return render_template('shopping.html', user_email=user_email)


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
            filtered_df = df[mask]
        else:
            mask = (df["date"] >= datetime.now().date() - timedelta(days=7))
            filtered_df = df[mask]
            if filtered_df.empty:
                filtered_df = df
        df = filtered_df
        purchases = df.to_dict(orient="records")
    return render_template('view_purchases.html', user_email=user_email, purchases=purchases)


@app.route('/show_graphs/<user_email>')
def show_graphs(user_email):
    return render_template('show_graphs.html', user_email=user_email)


@app.route('/show_graph/<user_email>/<graph_type>')
def show_graph(user_email, graph_type):
    file_path = os.path.join(DATA_DIR, f"{user_email}.csv")
    purchases = []
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df["date"], errors='coerce')
    df = df.dropna(subset=["date"])  # מוחק תאריכים לא חוקיים
    df["month"] = df["date"].dt.strftime('%Y-%m')  # YYYY-MM

    img_io = io.BytesIO()

    if graph_type == "monthly_expenses":
        plot_monthly_expenses(df, img_io)
    elif graph_type == "category_pie":
        plot_category_pie(df, img_io)
    elif graph_type == "current_vs_avg":
        plot_current_vs_avg(df, img_io)
    else:
        return "Invalid graph type", 400
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


@app.route('/optimize_shopping/<user_email>')
def optimize_shopping(user_email):
    with open("static/dummy_shop.html", encoding="utf-8") as fp:
        soup = BeautifulSoup(fp, "html.parser")
    products = soup.find_all("div", class_="product-card")
    store_prices = {}
    for product in products:
        name = product.find("h3").text.strip()
        price = product.find("p", class_="price").text.strip()
        price = float(price.replace("₪", "").replace(",", ""))
        store_prices[name] = price
    file_path = os.path.join(DATA_DIR, f"{user_email}.csv")
    if os.path.exists(file_path):
        user_purchases = pd.read_csv(file_path)
        cheaper_products = {}
        for _, row in user_purchases.iterrows():
            product_name = row["product"]
            user_price = row["price"]
            if product_name in store_prices and store_prices[product_name] < user_price:
                cheaper_products[product_name] = {
                    "product": product_name,
                    "user_price": user_price,
                    "store_price": store_prices[product_name]
                }
        cheaper_products = list(cheaper_products.values())
    else:
        cheaper_products = []
    return render_template('optimize_shopping.html', user_email=user_email, cheaper_products=cheaper_products)


@app.route('/view_dummy_user')
def view_dummy_user():
    size = 100
    product_category_map = {
        "לחם": "מאפים",
        "חלב": "מוצרי חלב",
        "ביצים": "מוצרי חלב",
        "גבינה": "מוצרי חלב",
        "אורז": "קטניות",
        "שמן": "תבלינים",
        "קפה": "משקאות",
        "תה": "משקאות",
        "פסטה": "קטניות",
        "עגבניות": "ירקות"
    }

    products = np.random.choice(list(product_category_map.keys()), size)
    categories = np.array([product_category_map[product] for product in products])
    quantities = np.random.randint(1, 11, size)
    prices = np.round(np.random.uniform(3, 30, size), 2)
    dates = pd.date_range(start=datetime.now() - timedelta(days=size), periods=size).strftime('%d-%m-%Y')

    df = pd.DataFrame({
        "product": products,
        "category": categories,
        "quantity": quantities,
        "price": prices,
        "date": dates
    })
    file_path = os.path.join(DATA_DIR, f"dummy_user.csv")
    df.to_csv(file_path, index=False)
    return render_template('view_purchases.html', purchases=df.to_dict(orient="records"), user_email="dummy_user")


if __name__ == '__main__':
    app.run(debug=True)
