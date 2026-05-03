import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import settings


def _send_email(to_email: str, subject: str, html_body: str):
    # Build the email message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
    msg["To"]      = to_email

    msg.attach(MIMEText(html_body, "html"))

    # Connect to Gmail SMTP and send
    with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
        server.ehlo()
        server.starttls()                                           # encrypt connection
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        server.sendmail(settings.MAIL_FROM, to_email, msg.as_string())

    print(f"Email sent to {to_email} | Subject: {subject}")


def send_verification_email(to_email: str, username: str, token: str):
    verify_link = f"{settings.BASE_URL}/verify-email?token={token}"

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background:#f4f4f4; padding:30px;">
        <div style="max-width:500px; margin:auto; background:#fff;
                    border-radius:8px; padding:30px; box-shadow:0 2px 8px rgba(0,0,0,0.1);">

          <h2 style="color:#333;">Hi {username}, Welcome!</h2>

          <p style="color:#555;">
            Thank you for registering. Please verify your email
            by clicking the button below.
          </p>

          <a href="{verify_link}"
             style="display:inline-block; padding:12px 24px;
                    background:#4CAF50; color:#fff; text-decoration:none;
                    border-radius:5px; font-size:16px;">
            Verify My Email
          </a>

          <p style="color:#999; margin-top:20px; font-size:13px;">
            This link expires in <strong>24 hours</strong>.<br>
            If you did not register, ignore this email.
          </p>

          <hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
          <p style="color:#aaa; font-size:12px;">
            Or copy this link into your browser:<br>
            <a href="{verify_link}" style="color:#4CAF50;">{verify_link}</a>
          </p>

        </div>
      </body>
    </html>
    """

    _send_email(to_email, "Verify Your Email — FastAPI Auth", html_body)


def send_welcome_email(to_email: str, username: str):
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background:#f4f4f4; padding:30px;">
        <div style="max-width:500px; margin:auto; background:#fff;
                    border-radius:8px; padding:30px; box-shadow:0 2px 8px rgba(0,0,0,0.1);">

          <h2 style="color:#4CAF50;">Email Verified Successfully!</h2>

          <p style="color:#555;">
            Hi <strong>{username}</strong>, your email has been verified.<br>
            You can now login to your account.
          </p>

          <p style="color:#999; font-size:13px;">Welcome to FastAPI Auth!</p>

        </div>
      </body>
    </html>
    """

    _send_email(to_email, "Email Verified — Welcome to FastAPI Auth!", html_body)
