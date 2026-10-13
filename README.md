# BookLeaf Publishing — Author Support & Communication Portal

An AI-powered author support and operations workflow portal built for BookLeaf Publishing to streamline author inquiries, automate triage, and draft policy-accurate responses.

---

## 1. Project Overview & Features

### A. Author Portal (Author-Facing)
- Role-Based Authentication: Secure login system where authors access only their own published catalog and ticket interactions.
- Catalog & Royalty Telemetry ("My Books"): Displays published titles, ISBNs, current lifecycle status, retail pricing, unit sales, earned royalties, paid payouts, and pending balances.
- Ticket Submission: Authors can raise queries linked directly to specific titles or flagged as account-level issues.
- Real-Time Ticket Tracking: Interactive thread view displaying ticket lifecycle states (Open, In Progress, Resolved, Closed) and responses.

### B. Admin Operations Portal (Admin-Facing)
- Central Triage Queue: Operational overview of all author queries filterable by lifecycle status and classification category.
- AI Ticket Auto-Classification: Automatically parses ticket subject and body into 6 operational categories: Royalty & Payments, ISBN & Metadata Issues, Printing & Quality, Distribution & Availability, Book Status & Production Updates, and General Inquiry.
- AI Priority Scoring: Assigns urgency tiers (Critical, High, Medium, Low) based on issue severity.
- Knowledge-Base Aware AI Draft Generation: Context-grounded response drafts reflecting BookLeaf operational policies (80/20 net profit split, quarterly disbursement within 45 days, minimum ₹1,000 threshold, reprint verification workflows, and stock sync timelines).
- Operations Control: Real-time status overrides, category/priority re-tagging, and internal staff notes hidden from the author view.

---

## 2. Technical Stack & Architectural Decisions

- Backend: Python / FastAPI (Asynchronous performance, native Pydantic validation, and automatic OpenAPI Swagger documentation generation).
- Database: SQLite + SQLAlchemy ORM (Clean relational data modeling across Users, Books, Tickets, and TicketMessages with migration portability).
- Frontend: HTML5, Tailwind CSS, Vanilla JS (Single Page Application with continuous background polling for near real-time updates).
- AI Integration: Context-Engineered LLM + Heuristic Engine (Dual-layer architecture with rule-based deterministic fallback for 100% system uptime during API rate limits).
- Security: JWT + Bcrypt (Stateless role-based access control protecting all REST routes).

---

## 3. Pre-Seeded Test Credentials

The database is pre-seeded using the provided BookLeaf catalog dataset (10 authors, 18 books):

- Admin Operations: admin@bookleafpub.com | Password: admin123
- Author (Priya Sharma): priya.sharma@email.com | Password: author123 (Books: Whispers of the Ganges, The Saffron Diaries)
- Author (Rohit Kapoor): rohit.kapoor@email.com | Password: author123 (Books: Code & Karma, Startup Sutra)

---

## 4. Local Installation & Setup Guide (Windows)

Prerequisites: Python 3.10+ and Git installed.

Installation Steps:

1. Clone the repository:
   git clone https://github.com/Kuldeepkumar1289/bookleaf-support-portal.git
   cd bookleaf-support-portal

2. Setup virtual environment (Windows PowerShell):
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1

3. Install dependencies:
   pip install -r ..\requirements.txt

4. Seed the database:
   python seed.py

5. Start the server:
   uvicorn main:app --reload

6. Open in browser:
   - Web Application: http://127.0.0.1:8000/
   - Interactive Swagger API Documentation: http://127.0.0.1:8000/docs

---

## 5. API Reference

- POST /api/auth/login : Authenticates credentials and returns a signed JWT token.
- GET /api/author/books : Retrieves books and royalty ledger for the authenticated author.
- POST /api/tickets : Submits ticket, triggers AI classification and priority scoring.
- GET /api/author/tickets : Retrieves author-specific ticket thread list.
- GET /api/admin/tickets : Retrieves triage queue with status and category filtering.
- PATCH /api/tickets/{id} : Updates status, priority, category, or assignee.
- GET /api/admin/tickets/{id}/ai-draft : Generates knowledge-base grounded draft response.
- GET /api/tickets/{id}/messages : Fetches message stream (hides internal notes from authors).
- POST /api/tickets/{id}/messages : Appends message or internal note to thread.

---

## 6. Engineering Write-Up: Approach & Trade-Offs

- AI Resilience & Cost Awareness: High token efficiency by passing targeted ticket descriptions and relevant catalog metadata rather than indiscriminate conversation histories. Includes a heuristic rule engine so core ticketing remains operational even if LLM quotas are exhausted.
- Policy Adherence: AI drafts are directly grounded in BookLeaf's operational constraints (80/20 profit split, 45-day quarterly payout window, minimum ₹1,000 threshold, and 5–7 day turnaround for verified print reprints).
- Data Isolation: Strict role-based query isolation prevents cross-author data leakage.
- Production Evolution Roadmap: Real-time WebSockets/SSE layer, Vector Retrieval (RAG) for dynamic SOPs, and S3/GCS presigned file uploads for defect photos.
