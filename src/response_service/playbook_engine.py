from playbook_store import PlaybookStore


class PlaybookEngine:

    def __init__(self):

        self.store = PlaybookStore()

    def execute(self, incident):

        signal = incident["error"]

        playbook = self.store.get_playbook(signal)

        if not playbook:

            return {
                "incident_id": incident["id"],
                "action": "none",
                "status": "no_playbook"
            }

        action = playbook["action"]

        print("Executing action:", action)

        return {
            "incident_id": incident["id"],
            "action": action,
            "status": "success"
        }