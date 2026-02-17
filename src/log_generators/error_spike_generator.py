import time

service = "auth-service"


def log(msg):
    line = f"{service} ERROR {msg}"
    print(line)
    with open("app.log", "a") as f:
        f.write(line + "\n")


def main(count: int = 5):
    # Produce a small mix: first 3 normal, then errors to total `count`
    for i in range(count):
        if i < 3:
            log("request processed successfully")
            time.sleep(0.2)
        else:
            log("timeout after 5 retries")
            time.sleep(0.2)


if __name__ == "__main__":
    main(5)
