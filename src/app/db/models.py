from sqlalchemy import String, Column, Integer, Boolean, LargeBinary, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    active_order_id = Column(String(36), nullable=True)
    type = Column(Integer, nullable=False, default=0)

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
    description = Column(Text, nullable=True)
    cover = Column(LargeBinary, nullable=True)  # store cover image as blob (DB storage)
    cover_path = Column(String(400), nullable=True)  # filesystem path when using FS storage
    author = relationship("Author", back_populates="books")

class Order(Base):
    __tablename__ = "orders"
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    paid = Column(Boolean, default=False)

class BookOrderItem(Base):
    __tablename__ = "book_order_items"
    id = Column(String(36), primary_key=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    book_id = Column(String(36), ForeignKey("books.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

class UserBookLikes(Base):
    __tablename__ = "user_book_likes"
    book_id = Column(String(36), ForeignKey("books.id"), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    wishlist = Column(Boolean, default=False)
    favourite = Column(Boolean, default=False)

class UserBookReview(Base):
    __tablename__ = "user_book_reviews"
    id = Column(String(36), primary_key=True)
    book_id = Column(String(36), ForeignKey("books.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=True)

class Comment(Base):
    __tablename__ = "comments"
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    review_id = Column(String(36), ForeignKey("user_book_reviews.id"), nullable=False)
    content = Column(Text, nullable=True)

class CommentLike(Base):
    __tablename__ = "comment_likes"
    comment_id = Column(String(36), ForeignKey("comments.id"), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
