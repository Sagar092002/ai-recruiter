import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv(override=True)

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT_STR = os.getenv("SMTP_PORT")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

try:
    SMTP_PORT = int(SMTP_PORT_STR) if SMTP_PORT_STR else None
except ValueError:
    SMTP_PORT = None

def send_email(to_email: str, subject: str, body: str):
    """
    Sends email using SMTP (supports port 465 SSL).
    Returns (success: bool, error_message: str)
    """
    
    if not SMTP_SERVER or not SMTP_PORT_STR or not SMTP_EMAIL or not SMTP_PASSWORD:

        missing = []
        if not SMTP_SERVER: missing.append("SMTP_SERVER")
        if not SMTP_PORT: missing.append("SMTP_PORT")
        if not SMTP_EMAIL: missing.append("SMTP_EMAIL")
        if not SMTP_PASSWORD: missing.append("SMTP_PASSWORD")
        
        error = f"❌ SMTP configuration error. Missing or Invalid: {', '.join(missing)}"
        print(error) # Prints to terminal
        print(f"DEBUG: Found SERVER={SMTP_SERVER}, PORT={SMTP_PORT}, EMAIL={SMTP_EMAIL}")
        return False, error

    from email.utils import formatdate, make_msgid

    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg.attach(MIMEText(body, "plain"))

    try:
        print(f"📧 Attempting to send email to: {to_email}")
        print(f"📡 Using SMTP: {SMTP_SERVER}:{SMTP_PORT}")
        
        # ✅ PORT 465 → SMTP_SSL (NO starttls)
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.send_message(msg)
                print(f"✅ Email sent successfully to {to_email}")

        # ✅ PORT 587 → STARTTLS
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
                server.starttls()
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.send_message(msg)
                print(f"✅ Email sent successfully to {to_email}")

        return True, "Email sent successfully"

    except smtplib.SMTPAuthenticationError as e:
        error = f"❌ Authentication failed: {str(e)}"
        print(error)
        return False, error
    
    except smtplib.SMTPRecipientsRefused as e:
        error = f"❌ Recipient email rejected: {str(e)}"
        print(error)
        return False, error
    
    except Exception as e:
        error = f"❌ Email sending failed: {str(e)}"
        print(error)
        return False, error
