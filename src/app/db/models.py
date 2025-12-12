import sqlalchemy as sa
from sqlalchemy import String, Column, Integer, Boolean, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    active_order_id = Column(String(36), nullable=True)

class Author(Base):
    __tablename__ = "authors"
    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    books = relationship("Book", back_populates="author")

class Book(Base):
    __tablename__ = "books"
    id = Column(String(36), primary_key=True)
    author_id = Column(String(36), ForeignKey("authors.id"), nullable=True)
    isbn = Column(String(50), unique=True, nullable=True)
    title = Column(String(400), nullable=False)
    cover = Column(LargeBinary, nullable=True)  # store cover image as blob
    author = relationship("Author", back_populates="books")

