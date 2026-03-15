class Enricher:

    def process(self, event):

        event["region"] = "us-east-1"
        event["cluster"] = "prod-cluster"

        return event