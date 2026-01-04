import json
import re
import secrets
import string
from app.db import candidates_collection

QUIZ_BASE_URL = "https://ai-recruiter-859z6bd6jfqfxufktu79e9.streamlit.app/?token="
QUIZ_PDF_PATH = "uploads/quizzes/backend_quiz.pdf"

EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"


# -------------------------
# Resume Processing
# -------------------------
def extract_email_from_resume(resume_text: str):
    matches = re.findall(EMAIL_REGEX, resume_text)
    return matches[0].lower() if matches else None


def process_uploaded_resumes(resume_texts):
    candidates = []
    for text in resume_texts:
        candidates.append({
            "resume_text": text,
            "email": extract_email_from_resume(text)
        })
    return candidates


# -------------------------
# Selection Logic (LLM safe)
# -------------------------
def select_top_candidates(ai_output: str, min_candidates: int):
    try:
        candidates = json.loads(ai_output)
    except json.JSONDecodeError:
        start = ai_output.find("[")
        end = ai_output.rfind("]") + 1
        candidates = json.loads(ai_output[start:end])

    candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
    return candidates[:min_candidates]


# -------------------------
# Credentials & MongoDB
# -------------------------
def generate_password(length=8):
    chars = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(chars) for _ in range(length))


def generate_token():
    return secrets.token_urlsafe(16)


def store_shortlisted_candidates(candidates):
    stored = []

    for c in candidates:
        password = generate_password()
        token = generate_token()

        record = {
            "candidate": c["candidate"],
            "email": c["email"],
            "score": c["score"],
            "password": password,
            "quiz_token": token,
            "quiz_link": f"{QUIZ_BASE_URL}{token}",
            "status": "SHORTLISTED"
        }

        candidates_collection.insert_one(record)
        stored.append(record)

    return stored


def validate_candidate_login(email, password):
    return candidates_collection.find_one({
        "email": email,
        "password": password
    })


def get_candidate_by_token(token):
    return candidates_collection.find_one({
        "quiz_token": token
    })