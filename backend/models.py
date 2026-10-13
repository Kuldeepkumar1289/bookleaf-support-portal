import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(String, unique=True, index=True, nullable=True) # e.g. AUTH001
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="author") # 'author' or 'admin'
    phone = Column(String, nullable=True)
    city = Column(String, nullable=True)
    joined_date = Column(String, nullable=True)

    books = relationship("Book", back_populates="author")
    tickets = relationship("Ticket", back_populates="author")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(String, unique=True, index=True, nullable=False) # e.g. BK001
    author_id_fk = Column(Integer, ForeignKey("users.id"))
    
    title = Column(String, nullable=False)
    isbn = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    publication_date = Column(String, nullable=True)
    status = Column(String, nullable=False) # 'Published & Live', 'In Production...'
    mrp = Column(Float, nullable=True)
    author_royalty_per_copy = Column(Float, nullable=True)
    total_copies_sold = Column(Integer, default=0)
    total_royalty_earned = Column(Float, default=0.0)
    royalty_paid = Column(Float, default=0.0)
    royalty_pending = Column(Float, default=0.0)
    last_royalty_payout_date = Column(String, nullable=True)
    print_partner = Column(String, nullable=True)
    available_on = Column(Text, nullable=True) # Stored as comma-separated or JSON string

    author = relationship("User", back_populates="books")
    tickets = relationship("Ticket", back_populates="book")

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=True) # Optional (General tickets)
    
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, default="General Inquiry")
    priority = Column(String, default="Medium") # Critical, High, Medium, Low
    status = Column(String, default="Open") # Open, In Progress, Resolved, Closed
    assigned_admin_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    author = relationship("User", back_populates="tickets")
    book = relationship("Book", back_populates="tickets")
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")

class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_role = Column(String, nullable=False) # 'author' or 'admin'
    message = Column(Text, nullable=False)
    is_internal_note = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    ticket = relationship("Ticket", back_populates="messages")