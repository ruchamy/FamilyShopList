from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


class User():
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password


users = [
    User(id=1, email='user1@example.com', password='password1'),
    User(id=2, email='user2@example.com', password='password2'),
    User(id=3, email='user3@example.com', password='password3')
]


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = next((u for u in users if u.email == email and u.password == password), None)
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
        if any(u.email == email for u in users):
            return render_template('message.html', message="האימייל כבר קיים", url="/login", url_text="התחבר")
        new_ser = User(id=users[-1].id + 1,email=email, password=password)
        users.append(new_ser)
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/shopping/<user_email>')
def shopping(user_email):
    return render_template('shopping.html', user_email=user_email)


if __name__ == '__main__':
    app.run(debug=True)
