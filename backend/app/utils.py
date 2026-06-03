import re
import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def extract_merchant(raw_text: str, category: str = None) -> str:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return None

    if category == "air_travel":
        for line in lines[:5]:
            if "united" in line.lower():
                return "United Airlines"

    return lines[0]


def extract_amount(raw_text: str) -> float:
    patterns = [
        r"Total Charged\s*\$?([0-9,]+\.[0-9]{2})",
        r"TOTAL\s*\$?([0-9,]+\.[0-9]{2})",
        r"Total\s*\$?([0-9,]+\.[0-9]{2})",
        r"Amount\s*\$?([0-9,]+\.[0-9]{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))

    amounts = re.findall(r"\$([0-9,]+\.[0-9]{2})", raw_text)
    if amounts:
        return float(amounts[-1].replace(",", ""))

    return None


def extract_date(raw_text: str) -> str:
    patterns = [
        r"Charge Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        r"Issued:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        r"Posted Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        r"Check-In:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        r"Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            return match.group(1)

    return None
