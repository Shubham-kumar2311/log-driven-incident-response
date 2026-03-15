from abc import ABC, abstractmethod


class BaseRule(ABC):
    """Abstract base class for all detection rules."""

    rule_id: str = ""

    def configure(self, rule_id: str, params: dict) -> None:
        """Apply rulebook parameters. Subclasses override to use params."""
        self.rule_id = rule_id

    @abstractmethod
    def check(self, event: dict) -> dict | None:
        """Evaluate *event* and return a signal dict if triggered, else None."""
