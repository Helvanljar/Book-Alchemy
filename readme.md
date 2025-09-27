# 📚 Book Alchemy

A modern **Digital Library** built with **Flask**, **SQLite**, and **SQLAlchemy**.  
Manage authors, add books, rate them, search, sort, and even get **AI-powered recommendations** with Hugging Face + Open Library.  

> Created by [Helvanljar](https://github.com/Helvanljar)

---

## ✨ Features

- 👤 Add and manage authors (with birth & death dates).  
- 📚 Add and manage books (title, year, ISBN, rating, cover).  
- 🔎 Search books and authors with keyword search.  
- ↕️ Sort books by title, author, year, or rating.  
- 🗑 Delete books (auto-removes author if orphaned).  
- 🗑 Delete authors (auto-removes their books).  
- 🌙 Dark mode toggle.  
- 📖 Detailed modals for books & authors.  
- 🧠 AI recommendations:
  - 1️⃣ Hugging Face free model (`zephyr-7b-beta`) suggests new books.  
  - 2️⃣ Open Library API suggests similar works by subject.  
  - 3️⃣ Fallback: random book from your library.  
- 🖼 Cover validation (no broken placeholders).  
- ✅ Clean code (PEP8 + commented templates, JS, CSS).  

---

## 🏗️ Project Structure

```
Book-Alchemy/
│
├── app.py              # Flask app with routes & logic
├── data_models.py      # SQLAlchemy models
├── data/
│   └── library.db      # SQLite database
│
├── templates/          # Jinja2 templates
│   ├── home.html
│   ├── add_author.html
│   ├── add_book.html
│   ├── author_list.html
│   ├── author_detail.html
│   ├── book_detail.html
│   └── recommend.html
│
├── static/             # Frontend assets
│   ├── style.css
│   ├── script.js
│   └── default_cover.jpg
│
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the repo
```bash
git clone https://github.com/Helvanljar/Book-Alchemy.git
cd Book-Alchemy
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)
```

### 3. Install dependencies
```bash
pip install flask sqlalchemy flask_sqlalchemy pillow requests
```

### 4. Run the app
```bash
python app.py
```

Open [http://localhost:5002](http://localhost:5002) in your browser 🚀

---

## 🔮 Usage

- **Add authors** via ➕ button in sidebar.  
- **Add books** with title, year, ISBN, cover, and rating.  
- **Browse** with search + sorting.  
- **View details** by clicking books/authors.  
- **Get recommendations** via ✨ button:
  - Hugging Face AI → Open Library → random fallback.  

---

## 🧪 Tech Stack

- **Backend:** Flask, SQLAlchemy, SQLite  
- **Frontend:** HTML, CSS, JavaScript (Vanilla)  
- **AI Integration:** Hugging Face Inference API (free, no key)  
- **External Data:** Open Library API  



---

## 🙌 Credits

- [Flask](https://flask.palletsprojects.com/)  
- [SQLAlchemy](https://www.sqlalchemy.org/)  
- [Open Library](https://openlibrary.org/developers/api)  
- [Hugging Face](https://huggingface.co/models)  

---

## 📜 License

MIT License © [Helvanljar](https://github.com/Helvanljar)
