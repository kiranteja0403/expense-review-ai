import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database import SessionLocal
from backend.app.models import Submission, ExpenseItem
from backend.app.utils import extract_text_from_pdf

SUBMISSIONS_DIR = os.path.join("backend", "data", "submissions")


def process_receipts():
    db = SessionLocal()

    submissions = db.query(Submission).all()

    for submission in submissions:
        folder_name = submission.folder_name
        receipts_dir = os.path.join(SUBMISSIONS_DIR, folder_name, "receipts")

        if not os.path.exists(receipts_dir):
            print(f"Receipts folder not found for {folder_name}")
            continue

        expense_items = db.query(ExpenseItem).filter_by(submission_id=submission.id).all()

        for item in expense_items:
            file_path = os.path.join(receipts_dir, item.file_name)

            if not os.path.exists(file_path):
                print(f"Missing file: {file_path}")
                continue

            if item.file_name.lower().endswith(".pdf"):
                raw_text = extract_text_from_pdf(file_path)
                item.raw_text = raw_text
                print(f"Processed: {item.file_name}")

        db.commit()

    db.close()
    print("Receipt processing completed.")


if __name__ == "__main__":
    process_receipts()
