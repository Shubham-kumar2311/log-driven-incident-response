import smtplib
from email.mime.text import MIMEText

from config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_TO, EMAIL_CONFIG_VALID


class EmailNotifier:

    def send(self, incident):

        recipient_email = (
            incident.get("receiver_email")
            or incident.get("reciever_email")
            or EMAIL_TO
        )

        if not SMTP_USER or not SMTP_PASSWORD:
            print("SMTP config missing, skipping email")
            return

        if not recipient_email:
            print("Recipient email missing, skipping email")
            return

        subject = f"[INCIDENT] {incident['severity']} - {incident['service']}"

        body = f"""
Incident Alert

Service: {incident['service']}
Severity: {incident['severity']}
Event: {incident['event_type']}
Time: {incident['timestamp']}

Message:
{incident.get('message','')}
"""

        msg = MIMEText(body)

        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = recipient_email

        try:

            if not EMAIL_CONFIG_VALID:
                print("Email config missing")
                return
            
            # print(SMTP_PASSWORD, SMTP_USER, EMAIL_TO)

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
            print("Connected to SMTP server")
            server.starttls()

            print("Logging in to SMTP server...")
            
            server.login(SMTP_USER, SMTP_PASSWORD)

            server.sendmail(
                SMTP_USER,
                recipient_email,
                msg.as_string()
            )

            server.quit()

            print("Email alert sent")

        except Exception as e:
            print("Email sending failed:", e)