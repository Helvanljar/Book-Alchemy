from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configure database URI
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable track modifications for efficiency

# Initialize SQLAlchemy
db = SQLAlchemy()
db.init_app(app)

# Import models (to be added in next step)
from data_models import Author, Book