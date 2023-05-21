from flask import Flask, render_template, request, redirect, jsonify, session, flash
import sqlite3
import requests

app = Flask(__name__)
app.secret_key = 'user-password'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['DATABASE'] = 'books.db'


def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, '
                 'authors TEXT, page_count INTEGER, average_rating REAL, user_id INTEGER, FOREIGN KEY(user_id) '
                 'REFERENCES users(id))')
    conn.commit()
    conn.close()


def register_user(username, password):
    conn = get_db_connection()
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user_id', None)  # Clear any existing session data

        username = request.form['username']
        password = request.form['password']

        # Authenticate the user
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            return redirect('/books')
        else:
            flash('Invalid username or password.')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if existing_user:
            flash('Username already exists.')
        else:
            register_user(username, password)
            flash('Registration successful. Please log in.')
            return redirect('/')

    return render_template('register.html')


@app.route('/books', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        book_id = request.form['book_id']
        delete_book(book_id)

    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('index.html', books=books)


@app.route('/search', methods=['GET', 'POST'])
def search():
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        search_type = request.form.get('search_type')
        search_query = request.form.get('search_query')

        if search_type == 'isbn':
            # search by ISBN
            response = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=isbn:{search_query}')
        else:
            # search by title
            response = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=intitle:{search_query}')

        data = response.json()

        if 'items' in data:
            conn = get_db_connection()

            # Find the first book in the JSON response that has complete information and is not a summary book.
            for item in data['items']:
                book = item['volumeInfo']
                title = book.get('title')
                authors = ', '.join(book.get('authors', []))
                page_count = book.get('pageCount')
                average_rating = book.get('averageRating')
                description = book.get('description')

                # do not include books that are a summary of the book (ex, searching for 80/20 Running gives "Summary of 80/20")
                if description and search_query.lower() not in description.lower():
                    # Store the book in the database with the user ID
                    conn.execute(
                        'INSERT INTO books (title, authors, page_count, average_rating, user_id) VALUES (?, ?, ?, ?, ?)',
                        (title, authors, page_count, average_rating, session['user_id']))
                    conn.commit()

                    return redirect('/books')

            conn.close()

        error_message = 'No books found.'
        return render_template('error.html', error=error_message)

    return render_template('search.html')


@app.route('/search_title/<string:title>', methods=['GET'])
def search_title(title):
    if 'user_id' not in session:
        return redirect('/')

    response = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=intitle:{title}')
    data = response.json()

    if 'items' in data:
        books = []
        for item in data['items']:
            book = item['volumeInfo']
            title = book.get('title')
            authors = ', '.join(book.get('authors', []))
            page_count = book.get('pageCount')
            average_rating = book.get('averageRating')

            books.append({
                'title': title,
                'authors': authors,
                'page_count': page_count,
                'average_rating': average_rating
            })

        return render_template('search.html', books=books)
    else:
        error_message = 'No books found.'
        return render_template('error.html', error=error_message)


@app.route('/books/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'user_id' not in session:
        return redirect('/')

    conn = get_db_connection()
    conn.execute('DELETE FROM books WHERE id = ? AND user_id = ?', (book_id, session['user_id']))
    conn.commit()
    conn.close()

    return redirect('/books')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user_id', None)
    return redirect('/')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
