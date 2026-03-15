import random
from base_generator import generate_base_log, write_log, sleep_between_logs

SERVICE = "db-service"

QUERIES = ["SELECT * FROM users WHERE id=?", "INSERT INTO orders VALUES (?)",
           "UPDATE payments SET status=? WHERE id=?", "DELETE FROM sessions WHERE expired=true",
           "SELECT COUNT(*) FROM events GROUP BY service"]
DBS = ["users_db", "orders_db", "sessions_db"]


def run(mode="normal"):
    while True:
        query = random.choice(QUERIES)
        db = random.choice(DBS)
        latency = random.randint(5, 150)

        if mode == "error_spike" and random.random() < 0.5:
            latency = random.randint(800, 5000)
            level = "ERROR"
            event = "db.slow_query"
        elif random.random() < 0.03:
            latency = random.randint(500, 3000)
            level = "WARN"
            event = "db.slow_query"
        else:
            level = "INFO"
            event = "db.query"

        log = generate_base_log(
            SERVICE, "database", level, event,
            f"Query on {db}: {latency}ms",
            {"latency_ms": latency, "query": query, "database": db,
             "rows_affected": random.randint(0, 500)}
        )

        write_log(SERVICE, log)
        sleep_between_logs()
