import re
from datetime import datetime

LOG_PATTERN = r"(?P<date>\w+ \d+)\s(?P<service>[\w-]+)\s(?P<level>\w+)\s(?P<message>.+)"

def parse_raw_log(raw_log: str):
    match = re.match(LOG_PATTERN, raw_log)
    if not match:
        return {
            "parsed": False,
            "raw": raw_log
        }

    return {
        "parsed": True,
        "serviceName": match.group("service"),
        "logLevel": match.group("level"),
        "message": match.group("message"),
        "timestamp": datetime.utcnow().isoformat(),
        "raw": raw_log
    }
