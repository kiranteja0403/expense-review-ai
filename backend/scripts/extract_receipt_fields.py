import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database import SessionLocal
from backend.app.models import ExpenseItem
from backend.app.utils import extract_merchant, extract_amount, extract_date


def extract_fields():
    db = SessionLocal()

    items = db.query(ExpenseItem).all()

    for item in items:
        if not item.raw_text:
            continue

        item.merchant = extract_merchant(item.raw_text, item.category)
        item.amount = extract_amount(item.raw_text)
        item.date = extract_date(item.raw_text)

        print(f"Updated {item.file_name} -> merchant={item.merchant}, amount={item.amount}, date={item.date}")

    db.commit()
    db.close()
    print("Field extraction completed.")


if __name__ == "__main__":
    extract_fields()
