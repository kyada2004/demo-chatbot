import smtplib
from email.mime.text import MIMEText

# TODO: Replace with your email address and password
EMAIL_ADDRESS = "YOUR_EMAIL_ADDRESS"
EMAIL_PASSWORD = "YOUR_EMAIL_PASSWORD"

def send_email(to, subject, body):
    """Send an email."""
    if EMAIL_ADDRESS == "YOUR_EMAIL_ADDRESS" or EMAIL_PASSWORD == "YOUR_EMAIL_PASSWORD":
        return "Please configure your email address and password in app/features/email.py"

    try:
        # Set up the SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        # Create the email
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to

        # Send the email
        server.send_message(msg)
        server.quit()

        return "Email sent successfully."

    except Exception as e:
        print(f"[Email Error] {e}")
        return "I encountered an error while trying to send the email."
