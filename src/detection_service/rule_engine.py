import json
import logging

from config import RULEBOOK_PATH
from rules.base_rule import BaseRule
from rules.http_error_rule import HTTPErrorRule
from rules.latency_rule import LatencyRule
from rules.auth_failure_rule import AuthFailureRule
from rules.deployment_failure_rule import DeploymentFailureRule
from rules.db_slow_query_rule import DBSlowQueryRule
from rules.cache_error_rule import CacheErrorRule

logger = logging.getLogger("detection.rule_engine")

# Registry: maps rule_class name in rulebook → Python class
RULE_REGISTRY: dict[str, type[BaseRule]] = {
    "HTTPErrorRule": HTTPErrorRule,
    "LatencyRule": LatencyRule,
    "AuthFailureRule": AuthFailureRule,
    "DeploymentFailureRule": DeploymentFailureRule,
    "DBSlowQueryRule": DBSlowQueryRule,
    "CacheErrorRule": CacheErrorRule,
}


class RuleEngine:
    """Loads rules from rulebook.json, instantiates enabled rules, evaluates events."""

    def __init__(self, rulebook_path: str = RULEBOOK_PATH):
        self.rules: list[BaseRule] = []
        self._load_rulebook(rulebook_path)

    def _load_rulebook(self, path: str) -> None:
        try:
            with open(path, "r") as f:
                rulebook = json.load(f)
        except FileNotFoundError:
            logger.error("Rulebook not found at %s — falling back to empty ruleset", path)
            return
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON in rulebook %s: %s", path, exc)
            return

        for entry in rulebook.get("rules", []):
            rule_id = entry.get("id", "unknown")
            if not entry.get("enabled", True):
                logger.info("Rule %s is disabled, skipping", rule_id)
                continue

            class_name = entry.get("rule_class")
            cls = RULE_REGISTRY.get(class_name)
            if cls is None:
                logger.warning("Unknown rule_class '%s' for rule '%s', skipping", class_name, rule_id)
                continue

            instance = cls()
            instance.configure(rule_id, entry.get("params", {}))
            self.rules.append(instance)
            logger.info("Loaded rule: %s (%s)", rule_id, class_name)

        logger.info("Rule engine ready — %d rules loaded", len(self.rules))

    def evaluate(self, event: dict) -> list[dict]:
        signals: list[dict] = []
        for rule in self.rules:
            try:
                signal = rule.check(event)
                if signal:
                    signals.append(signal)
                    logger.info(
                        "Rule fired",
                        extra={"rule_id": rule.rule_id, "signal_type": signal.get("signal_type")},
                    )
            except Exception:
                logger.exception("Rule %s raised an exception", rule.rule_id)
        return signals