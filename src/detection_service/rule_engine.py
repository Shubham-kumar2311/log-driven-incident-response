from rules.http_error_rule import HTTPErrorRule
from rules.latency_rule import LatencyRule
from rules.auth_failure_rule import AuthFailureRule
from rules.deployment_failure_rule import DeploymentFailureRule
from rules.db_slow_query_rule import DBSlowQueryRule


class RuleEngine:

    def __init__(self):

        self.rules = [
            HTTPErrorRule(),
            LatencyRule(),
            AuthFailureRule(),
            DeploymentFailureRule(),
            DBSlowQueryRule()
        ]

    def evaluate(self, event):

        signals = []

        for rule in self.rules:

            signal = rule.check(event)

            if signal:
                signals.append(signal)

        return signals