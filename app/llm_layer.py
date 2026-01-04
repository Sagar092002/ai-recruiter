import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq LLM
llm = ChatGroq(
    temperature=0.2,
    model_name="llama-3.3-70b-versatile", # High-performance model for ranking
    groq_api_key=os.getenv("GROQ_API_KEY")
)

def rank_resumes(job_description: str, candidates: list[dict]) -> str:
    """
    ranks candidates based on job description using Groq LLM
    """

    formatted_candidates = ""
    for idx, c in enumerate(candidates, start=1):
        formatted_candidates += f"""
Candidate {idx}:
Email: {c['email']}
Resume:
{c['resume_text']}
"""

    prompt = f"""
You are an expert technical recruiter.

Job Description:
{job_description}

Below are candidate profiles with their EMAIL as unique identifier.

{formatted_candidates}

Instructions:
- Rank candidates from best to worst based on job fit
- Give score out of 100
- Return the EXACT email address provided for each candidate
- Return candidate name (extract from resume if available)
- Give a short reason for the score
- Respond ONLY with a valid JSON array in this exact format:

[
  {{
    "candidate": "John Doe",
    "email": "john.doe@gmail.com",
    "score": 95,
    "reason": "Strong Python and FastAPI experience"
  }},
  ...
]

Do NOT add any explanations, markdown formatting, or text outside the JSON array.
"""

    response = llm.invoke(prompt)
    return response.content
