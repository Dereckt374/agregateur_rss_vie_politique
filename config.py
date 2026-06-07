import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    mistral_api_key: str
    mistral_model: str
    smtp_user: str
    smtp_password: str
    email_from: str
    email_to: str


def load_config(require_smtp: bool = True) -> Config:
    required = ["MISTRAL_API_KEY"]
    if require_smtp:
        required += ["SMTP_USER", "SMTP_PASSWORD", "EMAIL_TO"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise ValueError(f"Variables d'environnement manquantes : {', '.join(missing)}")

    smtp_user = os.getenv("SMTP_USER", "")
    return Config(
        mistral_api_key=os.environ["MISTRAL_API_KEY"],
        mistral_model=os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
        smtp_user=smtp_user,
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        email_from=os.getenv("EMAIL_FROM", smtp_user),
        email_to=os.getenv("EMAIL_TO", ""),
    )
