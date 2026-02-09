import uuid
from parser import parse_raw_log
from logger import write_log

class LogProcessingService:

    def process(self, raw_log: str):
        write_log("logs/input_log.txt", raw_log)

        parsed = parse_raw_log(raw_log)

        if parsed.get("parsed"):
            parsed["eventID"] = str(uuid.uuid4())

        write_log("logs/output_log.txt", str(parsed))
        return parsed
