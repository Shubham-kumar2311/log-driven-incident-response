class Normalizer:

    def process(self, event):

        event_type = event["event_type"]

        if event_type == "auth.login_failed":
            event["normalized_type"] = "AUTH_FAILURE"
            event["severity"] = "HIGH"

        elif event_type == "http.request":

            status = event["metadata"].get("status", 200)

            if status >= 500:
                event["normalized_type"] = "HTTP_ERROR"
                event["severity"] = "HIGH"

            elif status >= 400:
                event["normalized_type"] = "HTTP_CLIENT_ERROR"
                event["severity"] = "MEDIUM"

            else:
                event["normalized_type"] = "HTTP_SUCCESS"
                event["severity"] = "LOW"

        else:
            event["normalized_type"] = event_type
            event["severity"] = "LOW"

        return event