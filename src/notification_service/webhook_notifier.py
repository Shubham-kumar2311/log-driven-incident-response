import requests
from config import WEBHOOK_URL


class WebhookNotifier:

    def send(self, incident):

        if not WEBHOOK_URL:
            return

        payload = {
            "text": f"""
🚨 INCIDENT ALERT

Service: {incident['service']}
Severity: {incident['severity']}
Type: {incident['event_type']}
Time: {incident['timestamp']}
"""
        }

        try:

            requests.post(WEBHOOK_URL, json=payload)

        except Exception as e:

            print("Webhook notification failed:", e)