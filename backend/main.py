import os
import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import jwt
from passlib.context import CryptContext

from database import engine, get_db, Base
from models import User, Book, Ticket, TicketMessage
from ai_service import analyze_ticket_with_ai, generate_ai_draft_response

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BookLeaf Support & Communication Portal API", version="1.0.0")

# Enable CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JWT_SECRET = os.getenv("JWT_SECRET", "bookleaf_super_secret_jwt_key_2026")
JWT_ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ----------------- PYDANTIC SCHEMAS -----------------
class LoginRequest(BaseModel):
    email: str
    password: str

class TicketCreateRequest(BaseModel):
    book_id: Optional[int] = None
    subject: str
    description: str

class MessageCreateRequest(BaseModel):
    message: str
    is_internal_note: bool = False

class TicketUpdateRequest(BaseModel):
    status: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    assigned_admin_name: Optional[str] = None

# ----------------- AUTH HELPERS -----------------
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(days=2)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# ----------------- AUTH ENDPOINTS -----------------
@app.post("/api/auth/login")
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email).first()
    if not user or not pwd_context.verify(creds.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    token = create_access_token({"sub": user.email, "role": user.role, "id": user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "author_id": user.author_id,
            "city": user.city
        }
    }

# ----------------- AUTHOR PORTAL ENDPOINTS -----------------
@app.get("/api/author/books")
def get_author_books(token: str, db: Session = Depends(get_db)):
    user = get_current_user(token, db)
    if user.role != "author":
        raise HTTPException(status_code=403, detail="Access denied")
    
    books = db.query(Book).filter(Book.author_id_fk == user.id).all()
    return books

@app.post("/api/tickets")
def create_ticket(req: TicketCreateRequest, token: str, db: Session = Depends(get_db)):
    user = get_current_user(token, db)
    
    # Book context lookup for intelligent prompt
    book_context_str = "None"
    if req.book_id:
        b = db.query(Book).filter(Book.id == req.book_id).first()
        if b:
            book_context_str = f"{b.title} (Status: {b.status}, ISBN: {b.isbn})"

    # AI Pipeline Execution
    category, priority = analyze_ticket_with_ai(req.subject, req.description, book_context_str)

    new_ticket = Ticket(
        author_id=user.id,
        book_id=req.book_id,
        subject=req.subject,
        description=req.description,
        category=category,
        priority=priority,
        status="Open"
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

@app.get("/api/author/tickets")
def get_author_tickets(token: str, db: Session = Depends(get_db)):
    user = get_current_user(token, db)
    tickets = db.query(Ticket).filter(Ticket.author_id == user.id).order_by(Ticket.created_at.desc()).all()
    
    res = []
    for t in tickets:
        res.append({
            "id": t.id,
            "subject": t.subject,
            "description": t.description,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "created_at": t.created_at,
            "book_title": t.book.title if t.book else "General / Account Level"
        })
    return res

# ----------------- ADMIN PORTAL ENDPOINTS -----------------
@app.get("/api/admin/tickets")
def get_all_tickets_queue(token: str, status_filter: Optional[str] = None, category_filter: Optional[str] = None, db: Session = Depends(get_db)):
    user = get_current_user(token, db)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required")
    
    query = db.query(Ticket)
    if status_filter and status_filter != "All":
        query = query.filter(Ticket.status == status_filter)
    if category_filter and category_filter != "All":
        query = query.filter(Ticket.category == category_filter)

    tickets = query.order_by(Ticket.created_at.desc()).all()
    
    out = []
    for t in tickets:
        out.append({
            "id": t.id,
            "author_name": t.author.name,
            "author_email": t.author.email,
            "subject": t.subject,
            "description": t.description,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "assigned_admin_name": t.assigned_admin_name,
            "created_at": t.created_at,
            "book_title": t.book.title if t.book else "General"
        })
    return out

@app.patch("/api/tickets/{ticket_id}")
def update_ticket(ticket_id: int, req: TicketUpdateRequest, token: str, db: Session = Depends(get_db)):
    user = get_current_user(token, db)
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if req.status: ticket.status = req.status
    if req.category: ticket.category = req.category
    if req.priority: ticket.priority = req.priority
    if req.assigned_admin_name is not None: ticket.assigned_admin_name = req.assigned_admin_name
    
    db.commit()
    db.refresh(ticket)
    return ticket

# ----------------- AI DRAFT GENERATOR ENDPOINT -----------------
@app.get("/api/admin/tickets/{ticket_id}/ai-draft")
def get_ai_draft(ticket_id: int, token: str, db: Session = Depends(get_db)):
    user = get_current_user(token, db)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    book_info = None
    if ticket.book:
        b = ticket.book
        book_info = {
            "title": b.title,
            "status": b.status,
            "total_copies_sold": b.total_copies_sold,
            "total_royalty_earned": b.total_royalty_earned,
            "royalty_pending": b.royalty_pending
        }

    draft = generate_ai_draft_response(
        ticket_subject=ticket.subject,
        ticket_description=ticket.description,
        author_name=ticket.author.name,
        book_context=book_info
    )
    return {"draft_response": draft}

# ----------------- TICKET MESSAGES / CHAT -----------------
@app.get("/api/tickets/{ticket_id}/messages")
def get_ticket_messages(ticket_id: int, token: str, db: Session = Depends(get_db)):
    user = get_current_user(token, db)
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if user.role != "admin" and ticket.author_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    msgs_query = db.query(TicketMessage).filter(TicketMessage.ticket_id == ticket_id)
    # Hide internal notes from Authors
    if user.role != "admin":
        msgs_query = msgs_query.filter(TicketMessage.is_internal_note == False)

    messages = msgs_query.order_by(TicketMessage.created_at.asc()).all()
    return messages

@app.post("/api/tickets/{ticket_id}/messages")
def post_ticket_message(ticket_id: int, req: MessageCreateRequest, token: str, db: Session = Depends(get_db)):
    user = get_current_user(token, db)
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if user.role != "admin" and ticket.author_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    new_msg = TicketMessage(
        ticket_id=ticket.id,
        sender_id=user.id,
        sender_role=user.role,
        message=req.message,
        is_internal_note=req.is_internal_note if user.role == "admin" else False
    )
    db.add(new_msg)

    # Auto transition ticket status
    if user.role == "admin" and not req.is_internal_note and ticket.status == "Open":
        ticket.status = "In Progress"

    db.commit()
    db.refresh(new_msg)
    return new_msg

@app.get("/")
def serve_frontend():
    return FileResponse("../frontend/index.html")