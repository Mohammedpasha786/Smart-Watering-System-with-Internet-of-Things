"""
notifier.py
Send email and SMS alerts for irrigation events.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def send_email_alert(to_email: str, subject: str, body: str, smtp_config: dict) -> bool:
    """
    Send an email notification.

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text email body
        smtp_config: dict with keys: smtp_server, smtp_port, email, email_password

    Returns:
        True if sent successfully
    """
    from_email = smtp_config.get("email")
    password = smtp_config.get("email_password")
    smtp_server = smtp_config.get("smtp_server", "smtp.gmail.com")
    smtp_port = smtp_config.get("smtp_port", 587)

    if not from_email or not password:
        logger.warning("Email credentials not configured. Skipping notification.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())
        logger.info(f"Email sent to {to_email}")
        return True
    except smtplib.SMTPException as e:
        logger.error(f"Email send failed: {e}")
        return False
