"""
Flask application for a simple Digital Library.
Features:
- Manage authors and books
- Search and sort books
- Delete books and authors
- Recommend books using AI (Hugging Face), Open Library, or random fallback
"""

import os
import random
from io import BytesIO

import requests
from PIL import Image
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    flash
)
from sqlalchemy.exc import SQLAlchemyError

from data_models import db, Author, Book


# -----------------------------------------------------------------------------
# Flask setup
# -----------------------------------------------------------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "replace-with-a-secure-random-key"  # Required for flash messages

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "library.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy with Flask app
db.init_app(app)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def validate_cover(url: str) -> str | None:
    """
    Check if a cover URL points to a valid image.
    Rejects Open Library's 1x1 placeholder.
    """
    try:
        response = requests.get(url, timeout=5, stream=True)
        if (
            response.status_code == 200
            and response.headers.get("Content-Type", "").startswith("image")
        ):
            img = Image.open(BytesIO(response.content))
            width, height = img.size
            if width > 1 and height > 1:
                return url
    except Exception:
        pass
    return None


def ai_recommendation(books: list[Book]) -> dict | None:
    """
    Try to generate a book recommendation using Hugging Face free inference API.
    """
    prompt = "Here are the books currently in my library:\n"
    for b in books:
        prompt += f"- \"{b.title}\" by {b.author.name}\n"
    prompt += "\nSuggest one more book I might like (just give title and author)."

    try:
        resp = requests.post(
            "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta",
            headers={"Content-Type": "application/json"},
            json={"inputs": prompt},
            timeout=15,
        )
        data = resp.json()

        if isinstance(data, list) and "generated_text" in data[0]:
            text = data[0]["generated_text"].strip()
            parts = text.split(" by ")

            title = (
                parts[0]
                .replace("Suggest one more book I might like:", "")
                .strip()
                .strip('"')
            )
            author = parts[1].strip() if len(parts) > 1 else "Unknown"

            return {
                "title": title,
                "author": author,
                "cover_url": url_for("static", filename="default_cover.jpg"),
                "reason": "AI suggestion from Hugging Face",
            }
    except Exception as e:
        print("AI recommendation failed:", e)

    return None


def openlibrary_recommendation(base_book: Book) -> dict | None:
    """
    Fetch a recommendation from Open Library using subjects of a base book.
    """
    if not base_book.isbn:
        return None

    try:
        resp = requests.get(
            f"https://openlibrary.org/api/books?bibkeys=ISBN:{base_book.isbn}&jscmd=data&format=json",
            timeout=5,
        )
        data = resp.json()
        key = f"ISBN:{base_book.isbn}"

        if key in data and "subjects" in data[key]:
            subject = data[key]["subjects"][0]["name"]

            search_resp = requests.get(
                f"https://openlibrary.org/subjects/{subject.lower().replace(' ', '_')}.json?limit=5",
                timeout=5,
            )
            rec_data = search_resp.json()

            if "works" in rec_data and rec_data["works"]:
                rec = random.choice(rec_data["works"])
                return {
                    "title": rec.get("title", "Unknown"),
                    "author": rec["authors"][0]["name"] if rec.get("authors") else "Unknown",
                    "cover_url": (
                        f"https://covers.openlibrary.org/b/id/{rec['cover_id']}-L.jpg"
                        if rec.get("cover_id")
                        else url_for("static", filename="default_cover.jpg")
                    ),
                    "reason": f"Because you liked '{base_book.title}'",
                }
    except Exception as e:
        print("Open Library recommendation failed:", e)

    return None


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    """
    Home page route.
    Supports search and sorting of books.
    """
    query = request.args.get("q", "")
    sort_by = request.args.get("sort", "title")

    books = Book.query

    if query:
        books = books.join(Author).filter(
            (Book.title.ilike(f"%{query}%")) | (Author.name.ilike(f"%{query}%"))
        )

    if sort_by == "author":
        books = books.join(Author).order_by(Author.name)
    elif sort_by == "year":
        books = books.order_by(Book.publication_year.desc().nullslast())
    elif sort_by == "rating":
        books = books.order_by(Book.rating.desc().nullslast())
    else:
        books = books.order_by(Book.title)

    books = books.all()
    authors = Author.query.order_by(Author.name).all()

    return render_template(
        "home.html",
        books=books,
        authors=authors,
        search_query=query,
        sort_by=sort_by,
    )


@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    """
    Add a new author (GET = form, POST = save).
    """
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        birth_date = request.form.get("birthdate") or None
        date_of_death = request.form.get("date_of_death") or None

        if not name:
            flash("Author name cannot be empty.", "error")
            return redirect(url_for("add_author"))

        existing = Author.query.filter_by(name=name).first()
        if existing:
            flash("Author already exists.", "error")
            return redirect(url_for("add_author"))

        try:
            author = Author(
                name=name,
                birth_date=birth_date,
                date_of_death=date_of_death,
            )
            db.session.add(author)
            db.session.commit()
            flash("Author added successfully!", "success")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("Failed to add author.", "error")
            print("DB error:", e)

        return redirect(url_for("home"))

    return render_template("add_author.html")


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    """
    Add a new book (GET = form, POST = save).
    """
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        publication_year = request.form.get("publication_year")
        isbn = (request.form.get("isbn") or "").strip()
        rating = request.form.get("rating")
        cover_url = request.form.get("cover_url")
        author_id = request.form.get("author_id")

        if not title or not author_id:
            flash("Title and author are required.", "error")
            return redirect(url_for("add_book"))

        if rating:
            try:
                rating = float(rating)
                if not (0 <= rating <= 10):
                    raise ValueError
            except ValueError:
                flash("Rating must be a number between 0 and 10.", "error")
                return redirect(url_for("add_book"))
        else:
            rating = None

        if cover_url:
            cover_url = validate_cover(cover_url)

        try:
            book = Book(
                title=title,
                publication_year=int(publication_year)
                if publication_year else None,
                isbn=isbn or None,
                rating=rating,
                cover_url=cover_url,
                author_id=int(author_id),
            )
            db.session.add(book)
            db.session.commit()
            flash("Book added successfully!", "success")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("Failed to add book.", "error")
            print("DB error:", e)

        return redirect(url_for("home"))

    authors = Author.query.order_by(Author.name).all()
    return render_template("add_book.html", authors=authors)


@app.route("/delete_book/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    """
    Delete a book from the database.
    If its author has no remaining books, delete the author as well.
    """
    book = Book.query.get_or_404(book_id)
    author = book.author

    db.session.delete(book)
    db.session.commit()

    if not author.books:
        db.session.delete(author)
        db.session.commit()

    flash("Book deleted successfully.", "success")
    return redirect(url_for("home"))


@app.route("/delete_author/<int:author_id>", methods=["POST"])
def delete_author(author_id):
    """
    Delete an author and all their books from the database.
    """
    author = Author.query.get_or_404(author_id)
    db.session.delete(author)
    db.session.commit()
    flash("Author deleted successfully.", "success")
    return redirect(url_for("home"))


@app.route("/recommend", methods=["GET"])
def recommend():
    """
    Get a book recommendation.
    """
    books = Book.query.all()
    if not books:
        return jsonify({
            "title": "No books available",
            "author": "",
            "cover_url": url_for("static", filename="default_cover.jpg"),
        })

    suggestion = ai_recommendation(books)

    if not suggestion:
        base_book = random.choice(books)
        suggestion = openlibrary_recommendation(base_book)

    if not suggestion:
        base_book = random.choice(books)
        cover = validate_cover(base_book.cover_url) if base_book.cover_url else None
        if not cover:
            cover = url_for("static", filename="default_cover.jpg")
        suggestion = {
            "title": base_book.title,
            "author": base_book.author.name,
            "cover_url": cover,
            "reason": "Random suggestion from your library",
        }

    return jsonify(suggestion)


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5002)
