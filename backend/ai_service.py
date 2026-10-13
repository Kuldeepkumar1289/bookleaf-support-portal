import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

BOOKLEAF_KNOWLEDGE_BASE = """
BookLeaf Publishing Knowledge Base & Operational Policies:
- Company Overview: Self-publishing company operating in India & US. Catalog of 22,000+ titles. In-house printing in Delhi, and print partners Repro India & Epitome Books.
- Royalty Policy: 80/20 split (80% net profit to author, 20% to BookLeaf). Net profit = MRP minus printing, platform commission (Amazon/Flipkart), and shipping. Calculated quarterly, paid within 45 days after quarter ends. Minimum payout threshold is Rs 1,000 (rolls over if below). Direct bank transfer.
- ISBN Policy: Unique ISBN assigned under BookLeaf imprint. Duplicate/wrong ISBN linking is treated as high priority and escalated to production team.
- Printing & Quality: Standard print turnaround is 5-7 business days. Misprints/binding issues get a free reprint after the author shares defect photos.
- Distribution: Listed on Amazon India, Flipkart, Amazon US/UK, BookLeaf Store. New listings go live in 7-10 business days. "Currently Unavailable" usually means a stock sync issue, fixed in 24-48 hours.
- Production Stages: Manuscript Received -> Editing -> Cover Design -> Typesetting -> Proofreading -> ISBN Assignment -> Printing -> Distribution Setup -> Published & Live. Delays typically occur during Cover Design (author approval) and Proofreading.
- Communication Tone: Empathetic, professional, partner-centric, specific dates/data, own company mistakes directly, transparent escalation with 24-48 hr timelines.
"""

VALID_CATEGORIES = [
    "Royalty & Payments",
    "ISBN & Metadata Issues",
    "Printing & Quality",
    "Distribution & Availability",
    "Book Status & Production Updates",
    "General Inquiry"
]

VALID_PRIORITIES = ["Critical", "High", "Medium", "Low"]

def fallback_classifier(subject: str, description: str):
    """Graceful degradation heuristics when LLM is unavailable or offline."""
    text = f"{subject} {description}".lower()
    
    # Priority Heuristics
    if any(k in text for k in ["not received", "unpaid", "missing", "terrible", "wrong isbn", "months"]):
        priority = "Critical" if "royalty" in text or "months" in text else "High"
    elif any(k in text for k in ["delay", "broken", "unavailable", "issue"]):
        priority = "High"
    elif any(k in text for k in ["when", "update", "how"]):
        priority = "Medium"
    else:
        priority = "Low"

    # Category Heuristics
    if any(k in text for k in ["royalty", "payment", "payout", "money", "earning", "bank"]):
        category = "Royalty & Payments"
    elif any(k in text for k in ["isbn", "barcode", "metadata"]):
        category = "ISBN & Metadata Issues"
    elif any(k in text for k in ["print", "binding", "paper", "cover quality", "blurry"]):
        category = "Printing & Quality"
    elif any(k in text for k in ["amazon", "flipkart", "unavailable", "stock", "listing", "store"]):
        category = "Distribution & Availability"
    elif any(k in text for k in ["typesetting", "proof", "production", "status", "stage"]):
        category = "Book Status & Production Updates"
    else:
        category = "General Inquiry"

    return category, priority

def analyze_ticket_with_ai(subject: str, description: str, book_details: str = "None"):
    """
    Classifies ticket and calculates priority score using LLM or Heuristics fallback.
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

    if not api_key:
        return fallback_classifier(subject, description)

    prompt = f"""
    You are an automated support ticket analyzer for BookLeaf Publishing.
    Analyze the incoming author query.
    
    Categories allowed: {VALID_CATEGORIES}
    Priorities allowed: {VALID_PRIORITIES}

    Subject: {subject}
    Description: {description}
    Related Book Context: {book_details}

    Return strict JSON with keys "category" and "priority" only.
    Example: {{"category": "Royalty & Payments", "priority": "High"}}
    """

    try:
        # Generic lightweight POST request supporting OpenAI compatible endpoint
        if os.getenv("OPENAI_API_KEY"):
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=6)
            if res.status_code == 200:
                data = res.json()["choices"][0]["message"]["content"]
                parsed = json.loads(data)
                cat = parsed.get("category", "General Inquiry")
                prio = parsed.get("priority", "Medium")
                return (cat if cat in VALID_CATEGORIES else "General Inquiry"), (prio if prio in VALID_PRIORITIES else "Medium")
    except Exception:
        pass

    return fallback_classifier(subject, description)


def generate_ai_draft_response(ticket_subject: str, ticket_description: str, author_name: str, book_context: dict = None):
    """
    Generates a context-aware empathetic draft response matching BookLeaf knowledge base policies.
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

    context_str = "No specific book attached."
    if book_context:
        context_str = f"Book: '{book_context.get('title')}', Status: '{book_context.get('status')}', Copies Sold: {book_context.get('total_copies_sold')}, Royalty Earned: Rs {book_context.get('total_royalty_earned')}, Royalty Pending: Rs {book_context.get('royalty_pending')}"

    if not api_key:
        # Fallback intelligent templates
        text = f"{ticket_subject} {ticket_description}".lower()
        if "royalty" in text or "payment" in text:
            return (
                f"Dear {author_name},\n\nThank you for reaching out to us. We understand how important royalty payouts are to you.\n"
                f"As per BookLeaf's policy, royalties are calculated on an 80/20 net profit split and distributed quarterly within 45 days after the quarter closes (minimum payout threshold is ₹1,000).\n"
                f"According to your account data, your pending royalty stands at Rs {book_context.get('royalty_pending', '0') if book_context else '0'}. Our accounts team is reviewing the bank disbursement schedule and will update you within 48 hours.\n\nWarm regards,\nBookLeaf Support Team"
            )
        elif "unavailable" in text or "amazon" in text:
            return (
                f"Dear {author_name},\n\nThank you for bringing this to our attention. If your title is showing as 'Currently Unavailable', it is typically due to an inventory sync cycle between distributors.\n"
                f"We have triggered an immediate catalog re-sync with Amazon/Flipkart distribution, and listings normally resume active status within 24 to 48 hours.\n\nWarm regards,\nBookLeaf Support Team"
            )
        elif "print" in text or "quality" in text or "defect" in text:
            return (
                f"Dear {author_name},\n\nWe sincerely apologize for the quality issue you encountered with your author copies. Authors are our core partners, and we take print excellence seriously.\n"
                f"Could you please share photos showing the defect? Once verified, BookLeaf will arrange a complimentary reprint within 5-7 business days.\n\nWarm regards,\nBookLeaf Support Team"
            )
        else:
            return (
                f"Dear {author_name},\n\nThank you for reaching out to BookLeaf Publishing. We have received your query regarding '{ticket_subject}'.\n"
                f"Our operations team is actively looking into your account details and will provide a concrete update within 24-48 business hours.\n\nWarm regards,\nBookLeaf Support Team"
            )

    prompt = f"""
    {BOOKLEAF_KNOWLEDGE_BASE}

    You are a professional, empathetic senior support executive at BookLeaf Publishing.
    Draft an email response to an author query. Follow BookLeaf communication guidelines strictly.
    - Greet author warmly ({author_name}).
    - Acknowledge their concern with empathy.
    - Mention exact policy terms and account figures where relevant.
    - State a clear resolution next step and realistic timeline (e.g. 24-48 hours, 5-7 days for reprints).

    Author Query Subject: {ticket_subject}
    Author Query Description: {ticket_description}
    Author Book Context: {context_str}
    """

    try:
        if os.getenv("OPENAI_API_KEY"):
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=8)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    return f"Dear {author_name},\n\nThank you for contacting BookLeaf Support. We have logged your query regarding '{ticket_subject}'. Our team will review this and provide an update within 24-48 hours.\n\nWarm regards,\nBookLeaf Operations"