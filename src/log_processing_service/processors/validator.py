REQUIRED_FIELDS = [
    "event_id",
    "service_name",
    "timestamp",
    "log_level",
    "event_type"
]


class Validator:

    def process(self, event: dict):

        for field in REQUIRED_FIELDS:
            if field not in event:
                return None

        return event