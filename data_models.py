"""
Database models for the Digital Library application.
"""

from flask_sqlalchemy import SQLAlchemy

# Global SQLAlchemy instance, initialized in app.py
db = SQLAlchemy()


class Author(db.Model):
    """
    Represents an author of one or more books.

    Attributes:
        id (int): Primary key.
        name (str): Author's name (unique, not null).
        birth_date (date): Optional date of birth.
        date_of_death (date): Optional date of death.
        books (list[Book]): Relationship to Book model.
    """

    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    birth_date = db.Column(db.Date, nullable=True)
    date_of_death = db.Column(db.Date, nullable=True)

    books = db.relationship(
        "Book",
        backref="author",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Author {self.name}>"

    def __str__(self) -> str:
        life_span = f"{self.birth_date or '?'} – {self.date_of_death or ''}"
        return f"{self.name} ({life_span})"


class Book(db.Model):
    """
    Represents a book in the library.

    Attributes:
        id (int): Primary key.
        title (str): Book title (not null).
        publication_year (int): Optional year of publication.
        isbn (str): Optional ISBN.
        rating (float): Optional rating (0–10).
        cover_url (str): Optional cover image URL.
        author_id (int): Foreign key linking to Author.
    """

    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    publication_year = db.Column(db.Integer, nullable=True)
    isbn = db.Column(db.String(50), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    cover_url = db.Column(db.String(500), nullable=True)

    author_id = db.Column(
        db.Integer,
        db.ForeignKey("authors.id"),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Book {self.title}>"
