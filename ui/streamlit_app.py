# ============================================
# STREAMLIT FRONTEND – AI RECRUITER SYSTEM
# (HR Dashboard + Candidate Login + Quiz)
# ============================================

# ---------- FIX PYTHON PATH ----------
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------- STANDARD IMPORTS ----------
import streamlit as st
import pdfplumber
import copy

# ---------- PROJECT IMPORTS ----------
from app.llm_layer import rank_resumes
from app.backend_layer import (
    process_uploaded_resumes,
    select_top_candidates,
    store_shortlisted_candidates
)
from app.frontend_layer import show_second_round_email, generate_offer_letter
from app.email_service import send_email
from app.db import candidates_collection

# ============================================
# GLOBAL CONFIG
# ============================================
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads", "resumes")
QUIZ_PATH = os.path.join(PROJECT_ROOT, "uploads", "quizzes", "backend_quiz.pdf")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================
# TOKEN-BASED ROUTING & PAGE CONFIG
# ============================================
query_params = st.query_params
raw_token = st.query_params.get("token")
token = raw_token[0] if isinstance(raw_token, list) else raw_token
page = st.query_params.get("page", "home")

st.set_page_config(
    page_title="AI Recruiter System",
    page_icon="🤖",
    layout="wide" if not token else "centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Premium 'Touchy Dark' Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Poppins:wght@400;500;600;700&display=swap');
    
    /* ========================================
       THEME CONFIGURATION (Change colors here!)
    ======================================== */
    :root {
        --input-bg: #10101a;           /* Background of search box */
        --input-text: #ffffff;         /* Text color inside search box */
        --input-border: #6366f166;    /* Border color (66 is transparency) */
        --input-focus-bg: #10101a;     /* Background when clicking */
        --accent-glow: #6366f14d;     /* Shadow/Glow color */
        
        /* File Uploader Colors */
        --uploader-bg: rgba(10, 10, 15, 0.4);
        --uploader-border: rgba(99, 102, 241, 0.2);
        --uploader-btn-bg: #6366f1;
        --uploader-btn-text: #10101a;
        --uploader-file-text: white; /* Color for uploaded file names */
        
        /* Shortlisted Candidate Cards */
        --result-bg: #10101a;
        --result-hover-bg: rgba(99, 102, 241, 0.1);
    }
    
    /* ========================================
       NAVBAR STYLES
    ======================================== */
    .navbar {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 9999;
        background: rgba(5, 5, 5, 0.85);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding: 15px 5%;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    .navbar-logo {
        display: flex;
        align-items: center;
        gap: 12px;
        text-decoration: none;
        z-index: 10001;
    }
    
    .navbar-logo img {
        width: 45px;
        height: 45px;
        border-radius: 10px;
    }
    
    .navbar-logo-text {
        font-family: 'Poppins', sans-serif;
        font-size: 1.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }
    
    .navbar-menu {
        display: flex;
        gap: 40px;
        align-items: center;
        list-style: none;
        margin: 0;
        padding: 0;
    }
    
    .navbar-menu a {
        color: #94a3b8;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        position: relative;
        padding: 8px 0;
    }
    
    .navbar-menu a:hover {
        color: #ffffff;
    }
    
    .navbar-menu a::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 0;
        height: 2px;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        transition: width 0.3s ease;
    }
    
    .navbar-menu a:hover::after {
        width: 100%;
    }
    
    .navbar-login-btn {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important;
        padding: 10px 28px !important;
        border-radius: 50px !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
        border: none !important;
        display: inline-block !important;
    }
    
    .navbar-login-btn:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(99, 102, 241, 0.5) !important;
        filter: brightness(1.1);
    }

    /* Mobile Menu Toggle */
    .nav-toggle {
        display: none;
    }
    
    .nav-toggle-label {
        display: none;
        position: relative;
        height: 20px;
        width: 30px;
        cursor: pointer;
        z-index: 10001;
    }
    
    .nav-toggle-label span,
    .nav-toggle-label span::before,
    .nav-toggle-label span::after {
        display: block;
        background: #ffffff;
        height: 2px;
        width: 100%;
        border-radius: 10px;
        position: absolute;
        transition: all 0.3s ease;
    }
    
    .nav-toggle-label span::before {
        content: '';
        top: -8px;
    }
    
    .nav-toggle-label span::after {
        content: '';
        bottom: -8px;
    }

    /* Mobile Responsiveness */
    @media (max-width: 992px) {
        .navbar {
            padding: 15px 20px;
        }
        
        .nav-toggle-label {
            display: block;
        }
        
        .navbar-menu {
            position: absolute;
            top: 0;
            right: 0;
            width: 280px;
            height: 100vh;
            background: rgba(5, 5, 5, 0.98);
            backdrop-filter: blur(25px);
            flex-direction: column;
            justify-content: center;
            align-items: center;
            gap: 30px;
            transform: translateX(100%);
            transition: transform 0.4s cubic-bezier(0.77,0.2,0.05,1.0);
            box-shadow: -10px 0 30px rgba(0,0,0,0.5);
            z-index: 10000;
        }
        
        .nav-toggle:checked ~ .navbar-menu {
            transform: translateX(0);
        }
        
        .nav-toggle:checked + .nav-toggle-label span {
            background: transparent;
        }
        
        .nav-toggle:checked + .nav-toggle-label span::before {
            transform: rotate(45deg);
            top: 0;
        }
        
        .nav-toggle:checked + .nav-toggle-label span::after {
            transform: rotate(-45deg);
            bottom: 0;
        }
        
        .navbar-menu li {
            width: 100%;
            text-align: center;
        }
        
        .navbar-menu a {
            font-size: 1.1rem;
            display: block;
            width: 100%;
        }
        
        .navbar-login-btn {
            width: 80% !important;
            margin: 0 auto !important;
            font-size: 0.9rem !important;
        }

        .navbar-logo-text {
            font-size: 1.2rem;
        }
    }

    @media (max-width: 480px) {
        .navbar-logo-text {
            display: none;
        }
    }

    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #050505 !important;
        color: #e2e8f0;
        scroll-behavior: smooth;
    }
    
    /* Remove default padding and borders */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
        background-color: #050505 !important;
    }

    [data-testid="stAppViewContainer"] {
        background-color: #050505 !important;
    }

    /* Remove horizontal lines/dividers */
    hr {
        display: none !important;
    }

    [data-testid="stHorizontalBlock"] {
        border: none !important;
    }

    /* Remove any default Streamlit borders */
    .element-container {
        border: none !important;
    }

    /* Remove all dividers between sections */
    div[data-testid="stVerticalBlock"] > div {
        border: none !important;
    }

    /* Remove container borders */
    section[data-testid="stSidebar"] ~ div {
        border-top: none !important;
    }

    /* Force remove all top borders globally */
    * {
        border-top-color: transparent !important;
    }
    
    /* ========================================
       HERO SECTION - ENTERPRISE
    ======================================== */
    .hero-section {
        width: 100%;
        height: 85vh; /* 25% Increase in Landing Page Height */
        position: relative;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center; /* Centered Alignment */
        padding: 0 5%;
        background-color: #000000;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        text-align: center;
    }

    .hero-bg-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle at center, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
        z-index: 2;
    }

    .hero-content {
        position: relative;
        z-index: 3;
        max-width: 900px;
    }

    .hero-tagline {
        color: #6366f1;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 4px;
        font-size: 0.85rem;
        margin-bottom: 24px;
        display: block;
    }

    .hero-title {
        font-family: 'Poppins', sans-serif;
        font-size: 4rem;
        font-weight: 900;
        line-height: 1.1;
        margin-bottom: 20px;
        color: #ffffff;
        letter-spacing: -2px;
    }

    .hero-title span {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-description {
        font-size: 1.3rem;
        color: #94a3b8;
        line-height: 1.7;
        margin-bottom: 40px;
        max-width: 750px;
        margin-left: auto;
        margin-right: auto;
    }
    .form-section {
        background: #050505;
        padding: 0px 20px 80px 20px; /* Fully removed top padding */
        display: flex;
        flex-direction: column;
        align-items: center;
        border-top: none !important;
        margin-top: 0 !important;
    }
    
    .form-card {
        background: rgba(15, 15, 20, 0.8);
        border-radius: 32px;
        padding: 40px 60px;
        box-shadow: 0 40px 100px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-top: none !important; /* Remove top border line */
        max-width: 1100px;
        width: 100%;
        backdrop-filter: blur(20px);
        margin: 0 auto;
        margin-top: 0 !important;
    }
    
    .form-step-label {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 4px;
        font-size: 3rem;
        line-height: 1.5;
        margin-bottom: 30px;
        padding: 15px 0;
        display: block;
        text-align: center;
        filter: drop-shadow(0 0 20px rgba(99, 102, 241, 0.3));
    }
    
    .form-title {
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 30px;
        letter-spacing: -1.5px;
        text-align: center;
    }
    
    /* Input Overrides for Dark Mode - Premium Re-fit */
    [data-testid="stTextArea"] label, [data-testid="stNumberInput"] label, [data-testid="stFileUploader"] label, [data-testid="stTextInput"] label {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        margin-bottom: 12px !important;
    }

    /* Style Text Areas and Text Inputs */
    .stTextArea textarea, .stTextInput input {
        background: var(--input-bg) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 16px !important;
        padding: 15px 20px !important;
        color: var(--input-text) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        font-size: 1rem !important;
        line-height: 1.6 !important;
    }
    
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 25px var(--accent-glow) !important;
        background: var(--input-focus-bg) !important;
    }

    /* Selection Limit (Number Input) Style */
    [data-testid="stNumberInput"] {
        background-color: var(--input-bg) !important;
        border-radius: 16px !important;
        border: 1px solid var(--input-border) !important;
        padding: 5px 15px !important;
        transition: all 0.3s ease !important;
    }

    /* Target the white background specifically */
    [data-testid="stNumberInput"] div[data-baseweb="input"],
    [data-testid="stNumberInput"] input {
        background-color: #10101a !important;
        border: none !important;
    }

    [data-testid="stNumberInput"]:focus-within,
    [data-testid="stNumberInput"]:hover {
        border-color: #6366f1 !important;
        box-shadow: 0 0 25px var(--accent-glow) !important;
        background: var(--input-focus-bg) !important;
    }

    .stNumberInput input {
        color: var(--input-text) !important;
        font-weight: 600 !important;
    }

    /* File Uploader Premium Look */
    [data-testid="stFileUploader"] section {
        background: var(--uploader-bg) !important;
        border: 2px dashed var(--uploader-border) !important;
        border-radius: 20px !important;
        padding: 30px !important;
        transition: all 0.3s ease;
    }

    /* Style the 'Browse files' button specifically */
    [data-testid="stFileUploader"] button {
        background-color: var(--uploader-btn-bg) !important;
        color: var(--uploader-btn-text) !important;
        border: none !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stFileUploader"] button:hover {
        background-color: #4f46e5 !important; /* Slightly darker purple on hover */
        transform: scale(1.02);
    }

    [data-testid="stFileUploader"] section:hover {
        border-color: #6366f1 !important;
        background: rgba(99, 102, 241, 0.05) !important;
    }

    /* Style the list of uploaded files */
    [data-testid="stFileUploaderFile"] {
        color: var(--uploader-file-text) !important;
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 10px !important;
        margin-top: 10px !important;
        padding: 8px 15px !important;
    }

    [data-testid="stFileUploaderFileName"], 
    [data-testid="stFileUploaderFile"] small {
        color: var(--uploader-file-text) !important;
        opacity: 0.9 !important;
    }

    /* Centered Submit Button Container */
    .submit-container {
        display: flex;
        justify-content: center;
        margin-top: 40px;
        width: 100%;
    }

    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 100px !important;
        padding: 18px 45px !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 15px 35px rgba(99, 102, 241, 0.3) !important;
        width: auto !important;
        min-width: 320px !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 20px 50px rgba(99, 102, 241, 0.5) !important;
        filter: brightness(1.2);
    }

    /* Expander styling for results */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0a0a0c !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* ========================================
       SPLIT CONTENT LAYOUT
    ======================================== */
    .main-content {
        padding: 0px 40px 40px 40px; /* Removed top padding to eliminate gap */
        max-width: 1300px;
        margin: 0 auto;
    }
    
    .section-title {
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(to right, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.2rem;
        font-weight: 800;
        margin-top: 0 !important; /* Force remove top space */
        margin-bottom: 50px;
        letter-spacing: -1.5px;
        text-align: center;
    }
    
    .process-step {
        display: flex;
        align-items: flex-start;
        gap: 20px;
        margin-bottom: 24px;
        padding: 24px;
        background: rgba(255, 255, 255, 0.04); /* Permanent active background */
        border-radius: 18px;
        border: 1px solid rgba(99, 102, 241, 0.3); /* Permanent active border */
        transform: translateX(10px); /* Permanent active transform */
        transition: all 0.3s ease;
    }
    
    .process-step:hover {
        background: rgba(255, 255, 255, 0.06);
        border-color: #6366f1;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    
    .step-number {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 44px;
        height: 44px;
        background: rgba(99, 102, 241, 0.1);
        color: #818cf8;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1.1rem;
    }
    
    .step-content h3 {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0 0 6px 0 !important;
    }
    
    .step-content p {
        font-size: 0.95rem;
        color: #94a3b8;
        margin: 0 !important;
    }
    
    .visual-container {
        position: sticky;
        top: 20px;
    }
    
    .illustration-card {
        background: rgba(255, 255, 255, 0.01);
        border-radius: 30px;
        padding: 40px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-bottom: none !important; /* Remove bottom border */
        box-shadow: 0 50px 100px rgba(0, 0, 0, 0.5);
    }

    .main-content {
        border-bottom: none !important;
    }

    /* Text colors */
    h1, h2, h3, h4, p, span, label {
        color: #f1f5f9 !important;
    }
    
    /* Paragraph and List Styling */
    p, ol, ul, dl {
        margin: 0px 0px -2rem;
        padding: 0px;
        font-size: 1rem;
        font-weight: 400;
    }

    /* FORCE style for form submit button */
div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 100px !important;
    padding: 18px 45px !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    box-shadow: 0 15px 35px rgba(99, 102, 241, 0.3) !important;
}

/* Hover */
div[data-testid="stFormSubmitButton"] button:hover {
    background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
    filter: brightness(1.15);
}

    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================
# NAVBAR
# ============================================
from navbar_helper import get_base64_image

LOGO_PATH = r"C:/Users/asus/.gemini/antigravity/brain/3c7cbbca-9c5f-49b2-8770-3fc7dba0a253/recruitment_logo_1767452507640.png"

st.markdown(f"""
<nav class="navbar">
<div class="navbar-logo">
<img src="data:image/png;base64,{get_base64_image(LOGO_PATH)}" alt="Logo">
<span class="navbar-logo-text">AI Recruiter</span>
</div>
<input type="checkbox" id="nav-toggle" class="nav-toggle">
<label for="nav-toggle" class="nav-toggle-label">
<span></span>
</label>
<ul class="navbar-menu">
<li><a href="/?page=home" target="_self">Home</a></li>
<li><a href="/?page=about" target="_self">About</a></li>
<li><a href="/?page=home#login" class="navbar-login-btn" target="_self">Start Search</a></li>
</ul>
</nav>
""", unsafe_allow_html=True)



if token:
    # Check if we are on the quiz page or login page
    is_logged_in = st.session_state.get("candidate_logged_in", False)
    current_subpage = st.query_params.get("subpage", "login")

    # Common Premium Styles for Token-based pages
    st.markdown("""
        <style>
            /* Global Overrides for Page */
            .main { background-color: #050505 !important; }
            
            /* Typography & Font Sizes */
            h1 { font-size: 3.5rem !important; }
            h2 { font-size: 2.2rem !important; margin-bottom: 20px !important; }
            .stMarkdown p { font-size: 1.1rem !important; line-height: 1.6 !important; }
            
            /* Glassmorphism Card Style */
            .premium-card {
                background: rgba(255, 255, 255, 0.03);
                backdrop-filter: blur(15px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 24px;
                padding: 40px;
                margin-bottom: 30px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
                transition: transform 0.3s ease, border-color 0.3s ease;
            }
            .premium-card:hover {
                border-color: rgba(99, 102, 241, 0.4);
            }
            
            /* Quiz Question Card */
            .quiz-question-container {
                background: rgba(255, 255, 255, 0.02);
                border-left: 4px solid #6366f1;
                border-radius: 12px;
                margin-bottom: 25px;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                padding: 20px;
                cursor: pointer;
            }
            .quiz-question-container:hover {
                background: rgba(255, 255, 255, 0.05);
                border-left-color: #a855f7;
                transform: translateX(8px);
                box-shadow: 0 8px 30px rgba(99, 102, 241, 0.2);
            }
            
            /* Question Text Styling with Gradient Text Color */
            .quiz-question-container strong,
            .quiz-question-container p strong {
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                display: inline-block;
                font-size: 1.3rem !important;
                font-weight: 800 !important;
                transition: all 0.3s ease;
            }
            
            .quiz-question-container:hover strong,
            .quiz-question-container:hover p strong {
                filter: brightness(1.2);
                transform: scale(1.01);
            }
            
            /* Radio Button Tweak - Hide the "Select answer" label */
            div[data-testid="stRadio"] > label {
                display: none !important;
            }
            
            /* Add spacing between question text and radio options */
            div[data-testid="stRadio"] div[role="radiogroup"] {
                gap: 20px !important;
                margin-top: 32px !important;
            }

            /* Custom Radio Item Styling (Streamlit target) */
            div[data-testid="stMarkdownContainer"] strong {
                font-size: 1.2rem !important;
                color: #e2e8f0 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    if not is_logged_in or current_subpage == "login":
        # LOGIN PAGE LAYOUT
        st.markdown("""
            <style>
                .block-container {
                    padding-top: 120px !important;
                    max-width: 1250px !important;
                }
            </style>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1.1, 0.9], gap="large")

        with col1:
            # st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.markdown("""
                <h1 style="font-family: 'Poppins', sans-serif; font-weight: 800; letter-spacing: -2px; margin-bottom: 10px;">
                    🔐 <span style="background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Candidate Portal</span>
                </h1>
                <p style="color: #94a3b8; font-size: 1.1rem; margin-bottom: 40px;">Please authenticate to access your technical assessment.</p>
            """, unsafe_allow_html=True)

            email = st.text_input("Email Profile", placeholder="e.g. candidate@example.com").strip().lower()
            password = st.text_input("Secure Access Key", type="password", placeholder="••••••••")
            
            st.markdown('<div style="margin-top: 30px;">', unsafe_allow_html=True)
            if st.button("Enter Dashboard", use_container_width=True):
                candidate = candidates_collection.find_one({"quiz_token": token})
                if candidate:
                    stored_email = candidate["email"].lower()
                    stored_password = candidate["password"]

                    if stored_email == email and stored_password == password:
                        st.session_state["candidate_logged_in"] = True
                        st.query_params["subpage"] = "quiz"
                        st.rerun()
                    else:
                        st.error("❌ Identification failed. Please check your credentials.")
                else:
                    st.error("❌ Session expired or invalid token.")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            login_img_path = r"C:/Users/asus/.gemini/antigravity/brain/fc91c5b2-0984-4354-af74-6f4b718230a3/login_ai_avatar_1767498879681.png"
            st.image(login_img_path, use_container_width=True)
            st.markdown("""
                <div style="text-align: center; margin-top: 25px; padding: 20px; border-top: 1px solid rgba(255,255,255,0.05);">
                    <h3 style="color: #ffffff; font-size: 1.4rem; font-weight: 700;">AI-Match Intelligence</h3>
                    <p style="color: #6366f1; font-weight: 600; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px;">Verification Layer Active</p>
                </div>
            """, unsafe_allow_html=True)

    else:
        # QUIZ PAGE LAYOUT (AFTER REDIRECT)
        st.markdown("""
            <style>
                .block-container {
                    padding-top: 100px !important;
                    max-width: 900px !important;
                }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style="text-align: center; margin-bottom: 50px;">
                <h1 style="font-family: 'Poppins', sans-serif; font-weight: 900; letter-spacing: -2px;">
                    📝 <span style="background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Technical Assessment</span>
                </h1>
                <p style="color: #94a3b8; font-size: 1.2rem;">Demonstrate your expertise in core concepts.</p>
            </div>
        """, unsafe_allow_html=True)

        if "quiz_submitted" not in st.session_state:
            with st.form("quiz_form", border=False):
                # Instruction Box
                st.markdown("""
                    <div style="background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.2); padding: 20px; border-radius: 12px; margin-bottom: 40px;">
                        <p style="color: #e2e8f0; margin: 0; font-size: 1rem;">
                            <strong>Note:</strong> Select the correct option for each question. You need <strong>70%</strong> to qualify for the next round.
                        </p>
                    </div>
                """, unsafe_allow_html=True)

                answers = {}
                
                # Question UI Helper
                def render_question(num, q_text, key, options):
                    # st.markdown(f'<div class="quiz-question-container">', unsafe_allow_html=True)
                    st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); 
                                    -webkit-background-clip: text; 
                                    -webkit-text-fill-color: transparent; 
                                    font-size: 1.3rem; 
                                    font-weight: 800; 
                                    margin-bottom: 5px;
                                    display: inline-block;">
                            {num}. {q_text}
                        </div>
                    """, unsafe_allow_html=True)
                    ans = st.radio(f"Select answer for Q{num}", options, key=key, label_visibility="collapsed")
                    st.markdown('</div>', unsafe_allow_html=True)
                    return ans

                answers["q1"] = render_question(1, "What is the output of `2 ** 3` in Python?", "q1_key", ["6", "8", "9", "Error"])
                answers["q2"] = render_question(2, "Which keyword is used to define a function?", "q2_key", ["func", "define", "def", "function"])
                answers["q3"] = render_question(3, "Which of these is a mutable data type?", "q3_key", ["Tuple", "String", "List", "Integer"])
                answers["q4"] = render_question(4, "What is the correct file extension for Python files?", "q4_key", [".py", ".python", ".pt", ".txt"])
                answers["q5"] = render_question(5, "What does `len('Hello')` return?", "q5_key", ["4", "5", "0", "1"])

                st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
                submitted = st.form_submit_button("Complete & Submit Assessment", use_container_width=True)

                if submitted:
                    score = 0
                    if answers["q1"] == "8": score += 1
                    if answers["q2"] == "def": score += 1
                    if answers["q3"] == "List": score += 1
                    if answers["q4"] == ".py": score += 1
                    if answers["q5"] == "5": score += 1
                    
                    final_score = (score / 5) * 100
                    st.session_state["quiz_score"] = final_score
                    st.session_state["quiz_submitted"] = True
                    st.rerun()
        else:
            # RESULT SCREEN
            final_score = st.session_state["quiz_score"]
            
            # st.markdown('<div class="premium-card" style="text-align: center;">', unsafe_allow_html=True)
            st.markdown(f"""
                <h2 style="color: #ffffff;">Assessment Results</h2>
                <div style="font-size: 4rem; font-weight: 900; color: #6366f1; margin: 20px 0;">{final_score}%</div>
            """, unsafe_allow_html=True)

            if final_score >= 70:
                st.balloons()
                st.success("🎉 Outstanding! You have successfully passed the technical evaluation.")
                
                if "offer_sent" not in st.session_state:
                    with st.spinner("Compiling final offer package..."):
                        current_user = candidates_collection.find_one({"quiz_token": token})
                        if current_user:
                            user_email = current_user["email"]
                            user_name = current_user["candidate"]
                            subject, body = generate_offer_letter(user_name)
                            success, msg = send_email(user_email, subject, body)
                            if success:
                                st.session_state["offer_sent"] = True
                                st.markdown(f"""
                                    <div style="margin-top: 20px; padding: 15px; background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 8px; color: #10b981;">
                                        ✅ Offer Letter successfully dispatched to <strong>{user_email}</strong>.
                                    </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.error(f"❌ Dispatch error: {msg}")
                if st.session_state.get("offer_sent"):
                    st.info("Please check your primary inbox and spam folder for the next steps.")
            else:
                st.markdown("""
                    <div style="margin-top: 20px; padding: 15px; background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; border-radius: 8px; color: #ef4444;">
                        ❌ Score requirement not met. We encourage you to refine your skills and re-apply in the future.
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

# ============================================
# HR DASHBOARD CONTENT
# ============================================
st.markdown('<div class="main-content-wrapper">', unsafe_allow_html=True)

if page == "about":
    # ============================================
    # ABOUT PAGE: THE FUTURE OF AUTOMATION
    # ============================================
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    col_split1, col_split2 = st.columns([1, 1], gap="large")
    
    with col_split1:
        st.markdown('<h2 class="section-title">The Future of Automation</h2>', unsafe_allow_html=True)
        
        steps = [
            ("01", "JD Intelligence", "Define the ideal DNA of your candidate in seconds with the platform's advanced profile builder."),
            ("02", "Neural Parsing", "Proprietary AI extracts skills, context, and intent from every resume with human-level accuracy."),
            ("03", "Semantic Ranking", "The engine ranks talent based on depth of experience, not just keyword matches."),
            ("04", "Elite Selection", "Identify the top 1% of your applicant pool instantly with AI-generated reasoning."),
            ("05", "Automated Outreach", "The system handles the heavy lifting of scheduling and candidate communication."),
            ("06", "Strategic Insights", "Get a complete dashboard of why each candidate was chosen for the final round.")
        ]
        
        for num, title, desc in steps:
            st.markdown(f"""
            <div class="process-step">
                <div class="step-number">{num}</div>
                <div class="step-content">
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_split2:
        st.markdown('<div class="visual-container">', unsafe_allow_html=True)
        dashboard_img_path = r"C:/Users/asus/.gemini/antigravity/brain/6fbc6a3c-93c6-4de4-9527-b6c47074775c/enterprise_dashboard_illustration_1767372168013.png"
        
        st.image(dashboard_img_path, use_container_width=True)
        st.markdown("""
        <div style="margin-top: 25px; text-align: center;">
            <h4 style="color: #ffffff !important; margin-bottom: 8px; font-weight: 700;">Talent Analytics OS</h4>
            <p style="color: #94a3b8 !important; font-size: 0.95rem;">Experience a unified command center designed for modern talent acquisition teams.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True) # Close main-content
    st.stop() # Exclusive view for About page
else:
    # ============================================
    # HOME PAGE: HERO SECTION + FORM
    # ============================================
    st.markdown(f"""
    <div class="hero-section">
        <div class="hero-bg-overlay"></div>
        <div class="hero-content">
            <span class="hero-tagline">AI-DRIVEN RECRUITMENT</span>
            <h1 class="hero-title">Precision Hiring <span>at Scale.</span></h1>
            <p class="hero-description">
                Revolutionize your talent acquisition with deep neural parsing and semantic ranking. 
                Automate the lifecycle of high-volume hiring with elite pinpoint accuracy.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CSS for Hero Image
    st.markdown(f"""
    <style>
        .hero-section {{
            background-image: linear-gradient(90deg, #050505 0%, rgba(5, 5, 5, 0.7) 50%, transparent 100%), url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop');
            background-size: cover;
            background-position: center;
        }}
    </style>
    """, unsafe_allow_html=True)

    # --------------------------------------------
    # RECRUITMENT FORM SECTION
    # --------------------------------------------
    st.markdown('<div class="form-section" id="login">', unsafe_allow_html=True)
    st.markdown('<span class="form-step-label">AI Recruiter Engine</span>', unsafe_allow_html=True)
    st.markdown('<h2 class="form-title">Start Your Search</h2>', unsafe_allow_html=True)

# Form inside the card
job_description = st.text_area(
    "1. Define Target Role & Requirements",
    height=180,
    placeholder="e.g. Senior Backend Engineer with Expertise in Python, MongoDB and AI...",
    label_visibility="visible"
)

st.markdown('<div style="margin: 30px 0;"></div>', unsafe_allow_html=True) 

col_f1, col_f2 = st.columns([2, 1], gap="medium")
with col_f1:
    uploaded_files = st.file_uploader(
        "2. Candidate Pool (Upload PDF Resumes)",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="visible"
    )
with col_f2:
    min_candidates = st.number_input(
        "3. Selection Limit",
        min_value=1,
        max_value=50,
        value=3,
        step=1,
        help="How many top candidates to extract?"
    )

st.markdown('<div class="submit-container">', unsafe_allow_html=True)
process_clicked = st.button("🚀 Analyze & Match Talent", key="form_process_btn", use_container_width=False)
st.markdown('</div>', unsafe_allow_html=True)

# st.markdown('</div>', unsafe_allow_html=True) # Close form-card
st.markdown('</div>', unsafe_allow_html=True) # Close form-section

# ============================================
# HELPER FUNCTIONS
# ============================================
def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# ============================================
# PROCESSING LOGIC (Executed if button clicked)
# ============================================
if process_clicked:
    if not job_description.strip():
        st.error("❌ Job description is required.")
       
    elif not uploaded_files:
        st.error("❌ Please upload at least one resume.")
        
    else:
        # ----------------------------------------
        # SAVE & READ RESUMES
        # ----------------------------------------
        resume_texts = []

        with st.spinner("📄 Reading resumes..."):
            for file in uploaded_files:
                file_path = os.path.join(UPLOAD_DIR, file.name)
                with open(file_path, "wb") as f:
                    f.write(file.read())

                resume_texts.append(extract_text_from_pdf(file_path))

        # ----------------------------------------
        # BACKEND: EMAIL EXTRACTION
        # ----------------------------------------
        with st.spinner("📧 Extracting emails from resumes..."):
            processed_resumes = process_uploaded_resumes(resume_texts)

        # ----------------------------------------
        # LLM: RANKING
        # ----------------------------------------
        with st.spinner("🧠 AI is ranking candidates..."):
            ai_output = rank_resumes(
                job_description=job_description,
                candidates=processed_resumes
            )

        # ----------------------------------------
        # BACKEND: SHORTLIST
        # ----------------------------------------
        with st.spinner("🎯 Selecting top candidates..."):
            shortlisted = select_top_candidates(
                ai_output=ai_output,
                min_candidates=min_candidates
            )

        # ----------------------------------------
        # STORE IN MONGODB
        # ----------------------------------------
        with st.spinner("💾 Storing shortlisted candidates in MongoDB..."):
            stored_candidates = store_shortlisted_candidates(shortlisted)

        st.session_state["stored_candidates"] = stored_candidates
        st.success("✅ Candidates shortlisted and stored!")

# ============================================
# DISPLAY SHORTLISTED CANDIDATES (Full Width below columns)
# ============================================
if "stored_candidates" in st.session_state:
    st.write("")  # Spacer
    
    candidates = st.session_state["stored_candidates"]

    # ---------- DEBUG MODE ----------
    with st.sidebar:
        st.header("🛠️ Debug Mode")
        target_email = st.text_input("Override email (testing)")
        override = st.checkbox("Enable override")

    display_candidates = []

    for c in candidates:
        c_copy = copy.deepcopy(c)
        if override and target_email:
            c_copy["original_email"] = c_copy["email"]
            c_copy["email"] = target_email
        display_candidates.append(c_copy)

    # st.markdown('<div class="form-card">', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 40px;">
        <h2 style="font-family: 'Poppins', sans-serif; font-size: 2.8rem; font-weight: 800; letter-spacing: -1.5px; color: #ffffff;">
            📋 <span style="background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Shortlisted Candidates</span>
        </h2>
    </div>
    <style>
        /* Custom Styling for Results Expanders */
        [data-testid="stExpander"], [data-testid="stExpander"] > div, [data-testid="stExpander"] details {
            background-color: transparent !important;
            background: transparent !important;
            border: none !important;
        }

        /* Target the clickable header (summary) */
        .streamlit-expanderHeader, 
        [data-testid="stExpander"] summary {
            background: var(--result-bg) !important;
            border: 1px solid rgba(99, 102, 241, 0.3) !important;
            border-radius: 12px !important;
            padding: 18px 24px !important;
            margin-bottom: 12px !important;
            transition: all 0.3s ease !important;
            color: #ffffff !important;
        }

        .streamlit-expanderHeader p {
            background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
        }
        
        /* Active/Hover/Open State */
        .streamlit-expanderHeader:hover, 
        [data-testid="stExpander"] summary:hover,
        [data-testid="stExpander"] details[open] > summary {
            border-color: #6366f1 !important;
            background: var(--result-hover-bg) !important;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.4) !important;
        }
        
        /* Remove the background from the expanded content area */
        .streamlit-expanderContent {
            background: transparent !important;
            border: none !important;
            color: #94a3b8 !important;
            padding: 20px 25px !important;
        }

        /* Email Preview Box - Ultra Professional Spacing */
        .email-preview-box {
            background: #0a0a0f !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 16px !important;
            padding: 30px !important;
            color: #e2e8f0 !important; /* Brighter white-grey for clarity */
            font-family: 'Inter', -apple-system, sans-serif !important;
            font-size: 1rem !important;
            line-height: 1.8 !important;   /* Professional line spacing */
            letter-spacing: 0.3px !important; /* Professional character spacing */
            margin: 20px 0 !important;
            white-space: pre-wrap;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.5) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    for candidate in display_candidates:
        with st.expander(f"👤 {candidate['candidate']} | Score: {candidate['score']}"):

            if override and target_email:
                st.markdown(f"**Original Email:** {candidate.get('original_email')}")
                st.markdown(f"**Sending To:** {candidate['email']}")
            else:
                st.markdown(f"**Email:** {candidate['email']}")

            quiz_url = f"http://localhost:8501/?token={candidate['quiz_token']}"

            st.markdown(f"**🔐 Password:** `{candidate['password']}`")
            st.markdown(f"**📝 Quiz Link:** {quiz_url}")

            subject, body = show_second_round_email(candidate)

            st.markdown("""
            <h3 style="color: #ffffff; font-size: 1.2rem; margin-top: 30px; font-weight: 700; display: flex; align-items: center; gap: 10px;">
                📨 <span style="letter-spacing: 0.5px;">Email Preview</span>
            </h3>
            """, unsafe_allow_html=True)
            
            st.markdown(f'<div class="email-preview-box">{body}</div>', unsafe_allow_html=True)

            # Custom styled button for sending email
            col_btn, _ = st.columns([1.5, 2])
            with col_btn:
                if st.button(
                    f"📨 Send Official Email",
                    key=f"send_{candidate['quiz_token']}",
                    use_container_width=True
                ):
                    with st.spinner("Dispatching email..."):
                        success, message = send_email(
                            to_email=candidate["email"],
                            subject=subject,
                            body=body
                        )

                        if success:
                            st.success("✅ Email sent successfully")
                        else:
                            st.error(f"❌ {message}")
    
    # st.markdown('</div>', unsafe_allow_html=True)  # Close form-card

st.markdown('</div>', unsafe_allow_html=True)  # Close main-content-wrapper

# # End of Streamlit App

# # ============================================
# # STREAMLIT FRONTEND – AI RECRUITER SYSTEM
# # (HR Dashboard + Candidate Login + Online Quiz)
# # ============================================

