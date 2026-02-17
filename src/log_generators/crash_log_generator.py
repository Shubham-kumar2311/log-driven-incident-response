import time


def log(line):
    with open("app.log", "a") as f:
        f.write(line + "\n")
    print(line)


service = "payment-service"

def main(count: int = 5):
    # Prepare a simple stack-trace-style sequence and write up to `count` lines
    lines = [
        f"{service} ERROR NullPointerException",
        "  at com.payment.Service.process(Service.java:114)",
        "  at com.payment.Controller.handle(Controller.java:52)",
        "  at java.base/java.lang.Thread.run(Thread.java:829)",
        "  at java.base/java.lang.Thread.start(Thread.java:748)"
    ]

    for i in range(min(count, len(lines))):
        log(lines[i])
        time.sleep(0.1)


if __name__ == "__main__":
    main(5)
