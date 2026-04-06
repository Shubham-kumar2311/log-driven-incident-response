from fastapi import FastAPI
from notifier import Notifier
from models import Incident
from config import HOST, PORT

app = FastAPI(title="Notification Service")

notifier = Notifier()

notification_count = 0


@app.post("/notify")
def notify(incident: Incident):

    global notification_count

    notifier.notify(incident.dict())

    notification_count += 1

    return {
        "status": "notification_sent"
    }


@app.get("/health")
def health():

    return {
        "status": "notification service running"
    }


@app.get("/metrics")
def metrics():

    return {
        "notifications_sent": notification_count
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host=HOST, port=PORT, reload=False)