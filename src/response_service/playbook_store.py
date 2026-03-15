import json
import os


class PlaybookStore:

    def __init__(self):

        base = os.path.dirname(__file__)

        file_path = os.path.join(
            base,
            "playbooks",
            "playbooks.json"
        )

        with open(file_path) as f:
            self.playbooks = json.load(f)

    def get_playbook(self, signal_type):

        return self.playbooks.get(signal_type)