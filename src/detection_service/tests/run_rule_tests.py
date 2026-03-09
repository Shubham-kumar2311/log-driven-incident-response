import json
import requests
import time

URL = "http://localhost:8003/detect"

with open("rule_test_events.json") as f:
    events = json.load(f)

print("\nRunning detection rule tests\n")

for i, event in enumerate(events, 1):

    print("=" * 50)
    print(f"Event {i}: {event['event_type']}")

    # For auth test send multiple times
    if event["event_type"] == "auth.login_failed":

        print("Sending 5 auth failures to trigger rule")

        for j in range(5):
            response = requests.post(URL, json=event)
            print(f"Attempt {j+1}:", response.json())

    else:

        response = requests.post(URL, json=event)
        print(json.dumps(response.json(), indent=2))

    time.sleep(1)

print("\nAll tests completed\n")