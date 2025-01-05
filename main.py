from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
