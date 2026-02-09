from datetime import datetime

def write_log(filename, content):
    with open(filename, "a") as f:
        f.write(f"[{datetime.now()}] {content}\n")
