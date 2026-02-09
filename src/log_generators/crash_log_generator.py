import time
from datetime import datetime

def log(line):
    with open("app.log", "a") as f:
        f.write(line + "\n")
    print(line)

ts = datetime.now().strftime("%b %d %H:%M:%S")
service = "payment-service"

log(f"{ts} {service} ERROR NullPointerException")
log("  at com.payment.Service.process(Service.java:114)")
log("  at com.payment.Controller.handle(Controller.java:52)")
log("  at java.base/java.lang.Thread.run(Thread.java:829)")
