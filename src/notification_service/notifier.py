from webhook_notifier import WebhookNotifier
from email_notifier import EmailNotifier
from config import EMAIL_ENABLED


class Notifier:

    def __init__(self):

        self.webhook = WebhookNotifier()
        self.email = EmailNotifier()

    def notify(self, incident):

        severity = incident.get("severity", "LOW").upper()

        print("Notification received:", incident)

        if severity in ["CRITICAL", "HIGH"]:

            print("🚨 Sending critical alert")

            try:
                self.webhook.send(incident)
            except Exception as e:
                print("Webhook failed:", e)

            if EMAIL_ENABLED:
                try:
                    self.email.send(incident)
                except Exception as e:
                    print("Email failed:", e)

        else:

            print("ℹ️ Low severity incident:", incident)