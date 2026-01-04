def show_second_round_email(candidate):
    subject = "Shortlisted for Next Interview Round"

    body = f"""
Dear {candidate['candidate']},

Congratulations! You have been shortlisted for the next round.

Login Credentials:
Email: {candidate['email']}
Password: {candidate['password']}

Quiz Link:
{candidate['quiz_link']}

Please complete the quiz within the given time.

Best regards,
HR Team
"""

    return subject, body


def generate_offer_letter(candidate_name):
    subject = "🎉 Offer Letter: Congratulations!"

    body = f"""
Dear {candidate_name},

We are pleased to offer you the position at our company! 

Your performance in the technical quiz was outstanding (>70%).

Please reply to this email to accept the offer.
We look forward to working with you.

Best regards,
HR Manager
AI Recruiter System
"""
    return subject, body