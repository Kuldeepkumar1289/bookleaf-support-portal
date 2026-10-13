@"
# BookLeaf Author Support & Communication Portal

An intelligent, AI-assisted support portal and ticket operations workflow built for BookLeaf Publishing.

## 1. Project Overview
BookLeaf operates at a scale of 1,200+ monthly titles with thousands of active authors across India and the US. This system resolves author inquiry bottlenecks through:
- **Role-Based Portals**: Isolated dashboards for Authors (account & book telemetry) and Operations Admins (central triage).
- **AI-Powered Ticket Auto-Classification**: Automatically parses ticket subjects and descriptions into 6 operational categories with a priority score (Critical / High / Medium / Low).
- **Knowledge-Base Grounded AI Drafts**: Dynamically drafts empathetic responses referencing actual royalty splits (80/20), quarterly cycles (45-day window), print defect policies, and individual ledger balances.
- **Ticket Lifecycle Management**: Real-time message streaming, status transitions, priority overrides, and internal staff notes (hidden from authors).

---

## 2. Tech Stack & Architecture
- **Backend Framework**: Python FastAPI (Lightweight ASGI, automatic OpenAPI/Swagger specifications)
- **Database**: SQLite with SQLAlchemy ORM (Normalized tables: Users, Books, Tickets, TicketMessages)
- **AI Service**: Prompt-engineered LLM integration with heuristic rule fallback for zero-downtime reliability
- **Frontend**: Clean Single Page Application (HTML5, Tailwind CSS, Vanilla JS)
- **Authentication**: JWT-based session security with bcrypt password hashing

---

## 3. Pre-Seeded Test Credentials
Seeded directly from the official BookLeaf dataset:
- **Admin Operations**: \`admin@bookleafpub.com\` | Password: \`admin123\`
- **Author (Priya Sharma)**: \`priya.sharma@email.com\` | Password: \`author123\`
- **Author (Rohit Kapoor)**: \`rohit.kapoor@email.com\` | Password: \`author123\`

---

## 4. Local Installation & Run Guide
1. Clone the repository:
   \`\`\`bash
   git clone <REPO_URL>
   cd bookleaf-support-portal
   \`\`\`
2. Setup and activate virtual environment:
   \`\`\`bash
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   \`\`\`
3. Install dependencies:
   \`\`\`bash
   pip install -r ../requirements.txt
   \`\`\`
4. Seed the database with 10 authors and 18 books:
   \`\`\`bash
   python seed.py
   \`\`\`
5. Start the web server:
   \`\`\`bash
   uvicorn main:app --reload
   \`\`\`
6. Access endpoints:
   - Web Portal: \`http://127.0.0.1:8000/\`
   - Interactive Swagger API: \`http://127.0.0.1:8000/docs\`
"@ | Out-File -FilePath "README.md" -Encoding utf8