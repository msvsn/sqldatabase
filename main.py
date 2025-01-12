from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'supersecretkey'

DATABASE = 'database.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                surname TEXT NOT NULL,
                age INTEGER NOT NULL CHECK(age >= 0),
                city TEXT NOT NULL,
                hobby TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                surname TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                code TEXT
            )
        ''')
        conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        age = request.form['age']
        city = request.form['city']
        hobby = request.form['hobby']

        if int(age) < 0:
            return render_template('add.html', error="Вік не може бути від'ємним!")

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO people (name, surname, age, city, hobby) VALUES (?, ?, ?, ?, ?)',
                           (name, surname, age, city, hobby))
            conn.commit()

        return redirect(url_for('view'))

    return render_template('add.html')

@app.route('/view', methods=['GET'])
def view():
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')

    if sort_by not in ['id', 'name', 'surname', 'age', 'city', 'hobby']:
        sort_by = 'id'
    if order not in ['asc', 'desc']:
        order = 'asc'

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        query = f'SELECT * FROM people ORDER BY {sort_by} {order}'
        cursor.execute(query)
        people = cursor.fetchall()

    return render_template('view.html', people=people, sort_by=sort_by, order=order)

@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        ids_to_delete = request.form.getlist('delete_ids')
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            for person_id in ids_to_delete:
                cursor.execute('DELETE FROM people WHERE id = ?', (person_id,))
            conn.commit()

        return redirect(url_for('delete'))

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM people')
        people = cursor.fetchall()

    return render_template('delete.html', people=people)


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        phone = request.form['phone']
        email = request.form['email']

        code = str(random.randint(100000, 999999))

        if send_email(email, code):
            session['verification_code'] = code
            session['email'] = email

            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO feedback (name, surname, phone, email, code) VALUES (?, ?, ?, ?, ?)',
                               (name, surname, phone, email, code))
                conn.commit()

            flash('Verification code sent to your email.')
            return redirect(url_for('verify'))
        else:
            flash('Failed to send verification code. Please try again.')
            return redirect(url_for('feedback'))

    return render_template('feedback.html')


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        code = request.form['code']
        stored_code = session.get('verification_code')

        if not stored_code:
            flash('Verification code missing. Please try again.')
            return redirect(url_for('feedback'))

        if code == stored_code:
            flash('Verification successful!')
            return redirect(url_for('result'))
        else:
            flash('Invalid verification code. Please try again.')

    return render_template('verify.html')


@app.route('/roulette')
def result():
    titles = ['даун', 'іди нахуй', 'гніда', 'супер']
    assigned_title = random.choice(titles)
    return render_template('roulette.html', title=assigned_title)

def send_email(to_email, code):
    from_email = 'YOUR EMAIL'
    from_password = 'YOUR APP PASSWORD'

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = 'Verification Code'

    body = f'Your verification code is: {code}'
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, from_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f'Failed to send email: {e}')
        flash('Failed to send verification code. Please try again.')
        return False

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
