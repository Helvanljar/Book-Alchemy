from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Needed for flash messages

# Configure database URI
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy()
db.init_app(app)

# Import models
from data_models import Author, Book

# Create database tables (run once, then comment out)
with app.app_context():
    db.create_all()


@app.route('/')
def home():
    sort_by = request.args.get('sort_by', 'title')
    if sort_by == 'author':
        books = Book.query.join(Author).order_by(Author.name, Book.title).all()
    else:
        books = Book.query.order_by(Book.title).all()

    # Fetch cover images using Open Library API
    for book in books:
        response = requests.get(f"https://covers.openlibrary.org/b/isbn/{book.isbn}-M.jpg")
        book.cover_image = response.url if response.status_code == 200 else None

    return render_template('home.html', books=books)


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        name = request.form['name']
        birth_date = request.form['birthdate']
        date_of_death = request.form.get('date_of_death') or None

        new_author = Author(name=name, birth_date=birth_date, date_of_death=date_of_death)
        db.session.add(new_author)
        db.session.commit()
        flash('Author added successfully!', 'success')
        return redirect(url_for('add_author'))

    return render_template('add_author.html')


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        isbn = request.form['isbn']
        title = request.form['title']
        publication_year = request.form['publication_year']
        author_id = request.form['author_id']

        new_book = Book(isbn=isbn, title=title, publication_year=publication_year, author_id=author_id)
        db.session.add(new_book)
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('add_book'))

    authors = Author.query.all()
    return render_template('add_book.html', authors=authors)


# Seed data (run once, then comment out)
with app.app_context():
    if Author.query.count() == 0:
        authors = [
            Author(name="Jane Austen", birth_date="1775-12-16"),
            Author(name="George Orwell", birth_date="1903-06-25", date_of_death="1950-01-21"),
            Author(name="J.K. Rowling", birth_date="1965-07-31"),
            Author(name="Mark Twain", birth_date="1835-11-30", date_of_death="1910-04-21"),
            Author(name="Virginia Woolf", birth_date="1882-01-25", date_of_death="1941-03-28"),
        ]
        db.session.bulk_save_objects(authors)
        db.session.commit()

    if Book.query.count() == 0:
        books = [
            Book(isbn="9780141439518", title="Pride and Prejudice", publication_year=1813, author_id=1),
            Book(isbn="9780451524935", title="1984", publication_year=1949, author_id=2),
            Book(isbn="9780747532743", title="Harry Potter and the Philosopher's Stone", publication_year=1997,
                 author_id=3),
            Book(isbn="9780486284736", title="Adventures of Huckleberry Finn", publication_year=1884, author_id=4),
            Book(isbn="9780141182636", title="Mrs Dalloway", publication_year=1925, author_id=5),
        ]
        db.session.bulk_save_objects(books)
        db.session.commit()

if __name__ == '__main__':
    app.run(port=5002)