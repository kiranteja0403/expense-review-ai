import os
import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database import SessionLocal, engine
from backend.app.models import Base, Employee, Trip, Submission, ExpenseItem

SUBMISSIONS_DIR = os.path.join("backend", "data", "submissions")


def parse_trip_dates(trip_dates_str):
    if " to " in trip_dates_str:
        start_date, end_date = trip_dates_str.split(" to ")
        return start_date.strip(), end_date.strip()
    return None, None


def guess_category(filename):
    name = filename.lower()
    if "airlines" in name or "flight" in name:
        return "air_travel"
    if "marriott" in name or "hotel" in name:
        return "lodging"
    if "uber" in name or "taxi" in name or "airport" in name:
        return "ground_transport"
    if "dinner" in name or "lunch" in name or "breakfast" in name:
        return "meal"
    return "other"


def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print(f"Looking inside: {SUBMISSIONS_DIR}")

    for folder_name in os.listdir(SUBMISSIONS_DIR):
        folder_path = os.path.join(SUBMISSIONS_DIR, folder_name)

        if not os.path.isdir(folder_path):
            continue

        print(f"\nProcessing submission folder: {folder_name}")

        employee_info_path = os.path.join(folder_path, "employee_info.json")
        if not os.path.exists(employee_info_path):
            print(f"Missing employee_info.json in {folder_name}")
            continue

        with open(employee_info_path, "r", encoding="utf-8") as f:
            info = json.load(f)

        existing_employee = db.query(Employee).filter_by(employee_id=info["employee_id"]).first()

        if not existing_employee:
            employee = Employee(
                employee_id=info.get("employee_id"),
                name=info.get("name"),
                grade=info.get("grade"),
                title=info.get("title"),
                department=info.get("department"),
                manager_id=info.get("manager_id"),
                home_base=info.get("home_base"),
            )
            db.add(employee)
            db.commit()
            db.refresh(employee)
            print(f"Inserted employee: {employee.name}")
        else:
            employee = existing_employee
            print(f"Employee already exists: {employee.name}")

        start_date, end_date = parse_trip_dates(info.get("trip_dates", ""))

        trip = Trip(
            employee_id=employee.id,
            trip_purpose=info.get("trip_purpose"),
            start_date=start_date,
            end_date=end_date,
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)

        submission = Submission(
            trip_id=trip.id,
            folder_name=folder_name,
            status="seeded"
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

        receipts_dir = os.path.join(folder_path, "receipts")
        print(f"Receipts dir: {receipts_dir}")

        if os.path.exists(receipts_dir):
            receipt_files = os.listdir(receipts_dir)
            print(f"Found receipt files: {receipt_files}")

            for receipt_file in receipt_files:
                receipt_path = os.path.join(receipts_dir, receipt_file)

                if os.path.isfile(receipt_path):
                    expense_item = ExpenseItem(
                        submission_id=submission.id,
                        file_name=receipt_file,
                        category=guess_category(receipt_file),
                        merchant=None,
                        amount=None,
                        date=None,
                        raw_text=None,
                    )
                    db.add(expense_item)
                    print(f"Inserted expense item: {receipt_file}")

            db.commit()
        else:
            print(f"No receipts folder found for {folder_name}")

        print(f"Seeded submission and receipts: {folder_name}")

    db.close()
    print("\nSeeding completed.")


if __name__ == "__main__":
    seed_data()
