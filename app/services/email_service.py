
import os
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def send_email_otp(recipient_email: str, otp: str) -> bool:
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_APP_PASSWORD", "").replace(" ", "")

    if not sender_email or not sender_password:
        raise RuntimeError("SMTP credentials are missing from .env")

    message = EmailMessage()
    message["Subject"] = "Your Account Verification OTP"
    message["From"] = sender_email
    message["To"] = recipient_email

    message.set_content(
        f"""Hello,

Your account verification OTP is: {otp}

This OTP is valid for 5 minutes.
Please do not share this OTP with anyone.

If you did not request this OTP, please ignore this email.

Thank you.
"""
    )

    server = None

    try:
        print("Step 1: Connecting to Gmail on port 587...")

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=30
        )

        server.ehlo()

        print("Step 2: Starting TLS encryption...")

        server.starttls(context=ssl.create_default_context())
        server.ehlo()

        print("Step 3: Authenticating Gmail account...")

        server.login(sender_email, sender_password)

        print("Step 4: Authentication successful.")
        print("Step 5: Sending email...")

        server.send_message(message)

        print("Step 6: Email sent successfully!")

        return True

    except (smtplib.SMTPException, OSError) as error:
        print("SMTP operation failed.")
        print("Failure type:", type(error).__name__)
        print("Failure details:", str(error))
        raise RuntimeError("Failed to send OTP email") from error

    finally:
        if server is not None:
            try:
                server.quit()
            except (smtplib.SMTPException, OSError):
                pass
