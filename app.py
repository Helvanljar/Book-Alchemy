from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError
import os
import requests
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"

# Configure database URI
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Import db and models
from data_models import db, Author, Book

# Initialize SQLAlchemy
db.init_app(app)

# Create database tables
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Error creating database tables: {e}")


def get_book_recommendation(books):
    """
    Simulate an AI recommendation by selecting a book based on ratings or randomly.
    Replace with a real RapidAPI call in production.

    Args:
        books: List of Book objects from the database.

    Returns:
        dict: Recommended book details or None if no books available.
    """
    try:
        if not books:
            return None

        # Prefer books with high ratings (Bonus #4)
        rated_books = [book for book in books if book.rating is not None]
        if rated_books:
            # Select book with highest rating
            max_rating = max(book.rating for book in rated_books)
            top_rated = [book for book in rated_books if book.rating == max_rating]
            selected_book = random.choice(top_rated)
        else:
            # Fallback to random book if no ratings
            selected_book = random.choice(books)

        # Fetch cover image
        try:
            response = requests.get(
                f"https://covers.openlibrary.org/b/isbn/{selected_book.isbn}-M.jpg",
                timeout=5,
            )
            cover_image = response.url if response.status_code == 200 else None
        except requests.RequestException:
            cover_image = None

        return {
            "title": selected_book.title,
            "author": selected_book.author.name,
            "isbn": selected_book.isbn,
            "cover_image": cover_image,
            "reason": f"Recommended for its {'high rating' if selected_book.rating else 'popularity'}."
        }

    except Exception as e:
        print(f"Error generating recommendation: {e}")
        return None

    """
    To use a real AI API (e.g., RapidAPI ChatGPT-compatible API):
    1. Sign up for RapidAPI and get an API key.
    2. Choose an API like 'chatgpt-best-price' or similar.
    3. Replace this function with code like:

    import requests
    def get_book_recommendation(books):
        try:
            book_titles = [book.title for book in books]
            prompt = f"Recommend a book from this list based on ratings: {book_titles}"
            headers = {
                'X-RapidAPI-Key': 'YOUR_API_KEY',
                'X-RapidAPI-Host': 'chatgpt-best-price.p.rapidapi.com'
            }
            response = requests.post(
                'https://chatgpt-best-price.p.rapidapi.com/v1/completions',
                json={"prompt": prompt, "max_tokens": 100},
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            recommended_title = result['choices'][0]['text'].strip()
            selected_book = next((book for book in books if book.title == recommended_title), None)
            if selected_book:
                response = requests.get(
                    f"https://covers.openlibrary.org/b/isbn/{selected_book.isbn}-M.jpg",
                    timeout=5
                )
                cover_image = response.url if response.status_code == 200 else None
                return {
                    "title": selected_book.title,
                    "author": selected_book.author.name,
                    "isbn": selected_book.isbn,
                    "cover_image": cover_image,
                    "reason": "Recommended by AI based on your library."
                }
            return None
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            return None
        except Exception as e:
            print(f"Error generating recommendation: {e}")
            return None
    """


@app.route("/")
def home():
    """Render the homepage with sorted books and optional search."""
    sort_by = request.args.get("sort_by", "title")
    search = request.args.get("search", "").strip()

    try:
        query = Book.query
        if search:
            query = query.filter(Book.title.ilike(f"%{search}%"))

        if sort_by == "author":
            books = query.join(Author).order_by(Author.name, Book.title).all()
        else:
            books = query.order_by(Book.title).all()

        # Fetch cover images
        for book in books:
            try:
                response = requests.get(
                    f"https://covers.openlibrary.org/b/isbn/{book.isbn}-M.jpg",
                    timeout=5,
                )
                book.cover_image = response.url if response.status_code == 200 else None
            except requests.RequestException:
                book.cover_image = None

        authors = Author.query.all()
        return render_template("home.html", books=books, authors=authors)
    except Exception as e:
        flash(f"Error loading books: {str(e)}", "error")
        return render_template("home.html", books=[], authors=[])


@app.route("/book/<int:book_id>", methods=["GET", "POST"])
def book_detail(book_id):
    """Render and update details for a specific book."""
    try:
        book = Book.query.get_or_404(book_id)
        if request.method == "POST":
            try:
                rating = request.form.get("rating")
                if rating and rating.isdigit() and 1 <= int(rating) <= 10:
                    book.rating = int(rating)
                    db.session.commit()
                    flash(f"Rating updated for '{book.title}'!", "success")
                else:
                    flash("Invalid rating. Please enter a number between 1 and 10.", "error")
                return redirect(url_for("book_detail", book_id=book_id))
            except Exception as e:
                db.session.rollback()
                flash(f"Error updating rating: {str(e)}", "error")
                return redirect(url_for("book_detail", book_id=book_id))

        try:
            response = requests.get(
                f"https://covers.openlibrary.org/b/isbn/{book.isbn}-M.jpg", timeout=5
            )
            book.cover_image = response.url if response.status_code == 200 else None
        except requests.RequestException:
            book.cover_image = None
        return render_template("book_detail.html", book=book)
    except Exception as e:
        flash(f"Error loading book details: {str(e)}", "error")
        return redirect(url_for("home"))


@app.route("/author/<int:author_id>")
def author_detail(author_id):
    """Render details for a specific author."""
    try:
        author = Author.query.get_or_404(author_id)
        return render_template("author_detail.html", author=author)
    except Exception as e:
        flash(f"Error loading author details: {str(e)}", "error")
        return redirect(url_for("home"))


@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    """Handle adding a new author."""
    if request.method == "POST":
        try:
            name = request.form["name"].strip()
            birth_date = request.form["birthdate"]
            date_of_death = request.form.get("date_of_death") or None

            if not name:
                flash("Author name is required.", "error")
                return redirect(url_for("add_author"))

            new_author = Author(
                name=name, birth_date=birth_date, date_of_death=date_of_death
            )
            db.session.add(new_author)
            db.session.commit()
            flash("Author added successfully!", "success")
            return redirect(url_for("add_author"))
        except IntegrityError:
            db.session.rollback()
            flash("Error: Author could not be added due to a database issue.", "error")
            return redirect(url_for("add_author"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding author: {str(e)}", "error")
            return redirect(url_for("add_author"))

    return render_template("add_author.html")


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    """Handle adding a new book."""
    if request.method == "POST":
        try:
            isbn = request.form["isbn"].strip()
            title = request.form["title"].strip()
            publication_year = request.form["publication_year"]
            author_id = request.form["author_id"]

            if not isbn or not title or not publication_year or not author_id:
                flash("All fields are required.", "error")
                return redirect(url_for("add_book"))

            if not isbn.isdigit() or len(isbn) != 13:
                flash("ISBN must be a 13-digit number.", "error")
                return redirect(url_for("add_book"))

            new_book = Book(
                isbn=isbn,
                title=title,
                publication_year=int(publication_year),
                author_id=int(author_id),
            )
            db.session.add(new_book)
            db.session.commit()
            flash("Book added successfully!", "success")
            return redirect(url_for("add_book"))
        except IntegrityError:
            db.session.rollback()
            flash("Error: ISBN already exists.", "error")
            return redirect(url_for("add_book"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding book: {str(e)}", "error")
            return redirect(url_for("add_book"))

    try:
        authors = Author.query.all()
        return render_template("add_book.html", authors=authors)
    except Exception as e:
        flash(f"Error loading authors: {str(e)}", "error")
        return render_template("add_book.html", authors=[])


@app.route("/book/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    """Delete a book and its author if no other books remain."""
    try:
        book = Book.query.get_or_404(book_id)
        author_id = book.author_id
        book_title = book.title
        db.session.delete(book)
        db.session.commit()

        # Check if author has other books
        if not Book.query.filter_by(author_id=author_id).count():
            author = Author.query.get(author_id)
            if author:
                author_name = author.name
                db.session.delete(author)
                db.session.commit()
                flash(
                    f'Book "{book_title}" and author "{author_name}" deleted successfully!',
                    "success",
                )
            else:
                flash(f'Book "{book_title}" deleted successfully!', "success")
        else:
            flash(f'Book "{book_title}" deleted successfully!', "success")

        return redirect(url_for("home"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting book: {str(e)}", "error")
        return redirect(url_for("home"))


@app.route("/author/<int:author_id>/delete", methods=["POST"])
def delete_author(author_id):
    """Delete an author and their books."""
    try:
        author = Author.query.get_or_404(author_id)
        author_name = author.name
        db.session.delete(author)
        db.session.commit()
        flash(f'Author "{author_name}" and their books deleted successfully!', "success")
        return redirect(url_for("home"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting author: {str(e)}", "error")
        return redirect(url_for("home"))


@app.route("/recommend")
def recommend():
    """Render a book recommendation based on library contents."""
    try:
        books = Book.query.all()
        recommendation = get_book_recommendation(books)
        if recommendation:
            return render_template("recommend.html", recommendation=recommendation)
        else:
            flash("No books available for recommendation.", "error")
            return render_template("recommend.html", recommendation=None)
    except Exception as e:
        flash(f"Error generating recommendation: {str(e)}", "error")
        return render_template("recommend.html", recommendation=None)


def seed_data():
    """Seed the database with initial authors and books."""
    with app.app_context():
        try:
            if Author.query.count() == 0:
                authors = [
                    Author(name="Jane Austen", birth_date="1775-12-16"),
                    Author(
                        name="George Orwell",
                        birth_date="1903-06-25",
                        date_of_death="1950-01-21",
                    ),
                    Author(name="J.K. Rowling", birth_date="1965-07-31"),
                    Author(
                        name="Mark Twain",
                        birth_date="1835-11-30",
                        date_of_death="1910-04-21",
                    ),
                    Author(
                        name="Virginia Woolf",
                        birth_date="1882-01-25",
                        date_of_death="1941-03-28",
                    ),
                ]
                db.session.bulk_save_objects(authors)
                db.session.commit()

            if Book.query.count() == 0:
                books = [
                    Book(
                        isbn="9780141439518",
                        title="Pride and Prejudice",
                        publication_year=1813,
                        author_id=1,
                    ),
                    Book(
                        isbn="9780451524935",
                        title="1984",
                        publication_year=1949,
                        author_id=2,
                    ),
                    Book(
                        isbn="9780747532743",
                        title="Harry Potter and the Philosopher's Stone",
                        publication_year=1997,
                        author_id=3,
                    ),
                    Book(
                        isbn="9780486284736",
                        title="Adventures of Huckleberry Finn",
                        publication_year=1884,
                        author_id=4,
                    ),
                    Book(
                        isbn="9780141182636",
                        title="Mrs Dalloway",
                        publication_year=1925,
                        author_id=5,
                    ),
                ]
                db.session.bulk_save_objects(books)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding data: {e}")


if __name__ == "__main__":
    seed_data()
    app.run(port=5002)