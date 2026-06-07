import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_email(config, subject: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.email_from
    msg["To"] = config.email_to
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    logger.info("Envoi de l'email à %s via smtp.gmail.com:587…", config.email_to)
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(config.smtp_user, config.smtp_password)
        smtp.sendmail(config.email_from, [config.email_to], msg.as_string())
    logger.info("Email envoyé avec succès.")
