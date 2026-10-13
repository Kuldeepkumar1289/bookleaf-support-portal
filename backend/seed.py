import json
import os
from database import engine, SessionLocal, Base
from models import User, Book
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def run_seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # 1. Create Default Admin
    admin_user = User(
        name="BookLeaf Ops Admin",
        email="admin@bookleafpub.com",
        password_hash=pwd_context.hash("admin123"),
        role="admin",
        city="Delhi"
    )
    db.add(admin_user)
    db.commit()
    print("Created Admin: admin@bookleafpub.com (Password: admin123)")

    # 2. Ingest Sample Data
    json_path = "sample_data.json"
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found! Please place sample_data.json in backend directory.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    default_author_pass = pwd_context.hash("author123")

    for a_data in data.get("authors", []):
        author = User(
            author_id=a_data["author_id"],
            name=a_data["name"],
            email=a_data["email"],
            phone=a_data.get("phone"),
            city=a_data.get("city"),
            joined_date=a_data.get("joined_date"),
            password_hash=default_author_pass,
            role="author"
        )
        db.add(author)
        db.commit()
        db.refresh(author)

        for b_data in a_data.get("books", []):
            book = Book(
                book_id=b_data["book_id"],
                author_id_fk=author.id,
                title=b_data["title"],
                isbn=b_data.get("isbn"),
                genre=b_data.get("genre"),
                publication_date=b_data.get("publication_date"),
                status=b_data.get("status", "Draft"),
                mrp=b_data.get("mrp"),
                author_royalty_per_copy=b_data.get("author_royalty_per_copy"),
                total_copies_sold=b_data.get("total_copies_sold", 0),
                total_royalty_earned=b_data.get("total_royalty_earned", 0.0),
                royalty_paid=b_data.get("royalty_paid", 0.0),
                royalty_pending=b_data.get("royalty_pending", 0.0),
                last_royalty_payout_date=b_data.get("last_royalty_payout_date"),
                print_partner=b_data.get("print_partner"),
                available_on=",".join(b_data.get("available_on", []))
            )
            db.add(book)
        db.commit()

    db.close()
    print("Database seeding completed successfully with all 10 authors and books!")

if __name__ == "__main__":
    run_seed()