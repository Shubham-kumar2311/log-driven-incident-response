import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() in ["true","1","yes"]

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

EMAIL_TO = os.getenv("EMAIL_TO", "")

EMAIL_CONFIG_VALID = all([
    SMTP_USER,
    SMTP_PASSWORD,
    EMAIL_TO
])