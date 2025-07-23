import re
import pytesseract
import cv2
from PyPDF2 import PdfReader

# Extract text from PDF using PyPDF2
def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except:
        return ""

# Extract text from image using pytesseract
def extract_text_from_image(image_path):
    try:
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)
        return text.strip()
    except:
        return ""

# Extract name, email, phone, and skills from raw resume text
def extract_details(text):
    # Split lines before cleanup to preserve name line
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # 1. Extract name from the first valid line
    name = lines[0] if lines else "Unknown"
    if len(name.split()) < 2 or not name.replace(" ", "").isalpha():
        name = "Unknown"

    # Now clean the text for pattern-based matching
    clean_text = " ".join(lines)

    # 2. Extract email
    email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", clean_text)
    email = email_match.group() if email_match else "Unknown"

    # 3. Extract phone
    phone_match = re.search(r"\b(?:\+?\d{1,4}[-.\s]?)?(?:\(?\d{3,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}\b", clean_text)
    phone = phone_match.group() if phone_match else "Unknown"

    # 4. Extract skills (basic list matching)
    skill_keywords = [
        "python", "java", "c++", "c", "sql", "javascript", "react", "node.js",
        "machine learning", "deep learning", "aws", "html", "css", "salesforce", "data analysis"
    ]
    skills_found = [skill for skill in skill_keywords if skill in clean_text.lower()]
    skills = ", ".join(skills_found) if skills_found else "Not specified"

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills
    }
