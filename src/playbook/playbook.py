import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Callable


class StepExecutionError(Exception):
    pass


@dataclass
class PlaybookStep:
    step_id: str
    action_type: str
    target: str
    command: str
    retry_count: int = 1


@dataclass
class Playbook:
    playbook_id: str
    name: str
    trigger_severity: str
    steps: List[PlaybookStep] = field(default_factory=list)

    def add_step(self, step: PlaybookStep):
        self.steps.append(step)


class PlaybookEngine:
    def __init__(self):
        self._actuators: Dict[str, Callable[[str, str], bool]] = {}

    def register_actuator(self, action_type: str, handler: Callable[[str, str], bool]):
        self._actuators[action_type] = handler

    def execute(self, playbook: Playbook, incident_id: str) -> Dict:
        execution_id = str(uuid.uuid4())
        results = []

        for step in playbook.steps:
            result = self._execute_step(step)
            results.append(result)

        return {
            "execution_id": execution_id,
            "incident_id": incident_id,
            "playbook_id": playbook.playbook_id,
            "status": "completed" if all(r["success"] for r in results) else "failed",
            "steps": results
        }

    def _execute_step(self, step: PlaybookStep) -> Dict:
        if step.action_type not in self._actuators:
            raise StepExecutionError(f"No actuator registered for {step.action_type}")

        attempts = 0
        success = False
        error_message = None

        while attempts < step.retry_count and not success:
            attempts += 1
            try:
                success = self._actuators[step.action_type](step.command, step.target)
            except Exception as e:
                error_message = str(e)
                success = False

        return {
            "step_id": step.step_id,
            "action_type": step.action_type,
            "target": step.target,
            "command": step.command,
            "attempts": attempts,
            "success": success,
            "error": error_message
        }