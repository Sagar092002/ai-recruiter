"""
MAIN ENTRY POINT
----------------
This file connects:
- LLM layer (AI ranking)
- Backend layer (business logic)
- Frontend layer (email preview)

Run using:
python -m app.main
"""

from app.llm_layer import rank_resumes
from app.backend_layer import (
    process_uploaded_resumes,
    select_top_candidates,
    prepare_second_round
)
from app.frontend_layer import show_second_round_email


# --------------------------------------------------
# 1. INPUTS (Simulating HR uploading resumes)
# --------------------------------------------------

job_description = """
Backend Developer with Python, FastAPI, SQL.
Minimum 2 years of experience.
"""

# These simulate parsed PDF resume texts
# In Streamlit, these come from uploaded PDFs
resume_texts = [
    """
    John Doe
    Email: john.doe@gmail.com
    Python Backend Developer
    3 years experience with FastAPI, SQL, PostgreSQL
    """,

    """
    Neha Gupta
    Email: neha.gupta@outlook.com
    Python Engineer
    Experience with Django, REST APIs, PostgreSQL
    """,

    """
    Amit Sharma
    Email: amit.sharma@company.com
    Java Developer
    Spring Boot, Microservices
    """
]

print("\n📥 Processing uploaded resumes...\n")

# --------------------------------------------------
# 2. BACKEND: Extract email + prepare candidate data
# --------------------------------------------------

processed_candidates = process_uploaded_resumes(resume_texts)

"""
processed_candidates looks like:
[
  {
    "resume_text": "...",
    "email": "john.doe@gmail.com"
  },
  ...
]
"""

# --------------------------------------------------
# 3. LLM: Rank resumes (EMAIL IS PASSED TO LLM)
# --------------------------------------------------

print("🧠 AI is ranking candidates...\n")

ai_output = rank_resumes(
    job_description=job_description,
    candidates=processed_candidates
)

print("🔎 Raw AI Output:\n")
print(ai_output)
print("\n" + "-" * 60 + "\n")

# --------------------------------------------------
# 4. BACKEND: Select top N candidates safely
# --------------------------------------------------

MIN_CANDIDATES = 2

shortlisted_candidates = select_top_candidates(
    ai_output=ai_output,
    min_candidates=MIN_CANDIDATES
)

"""
shortlisted_candidates now already contains:
- candidate name
- email (correct one)
- score
- reason
"""

# --------------------------------------------------
# 5. BACKEND: Prepare second round (password + quiz)
# --------------------------------------------------

second_round_candidates = prepare_second_round(shortlisted_candidates)

# --------------------------------------------------
# 6. FRONTEND: Show email previews
# --------------------------------------------------

print("📧 SECOND ROUND EMAIL PREVIEWS\n")

for candidate in second_round_candidates:
    print(show_second_round_email(candidate))
    print("=" * 70)
