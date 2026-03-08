from rule_engine import RuleEngine


class DetectionPipeline:

    def __init__(self):

        self.rule_engine = RuleEngine()

    def process(self, event):

        signals = self.rule_engine.evaluate(event)

        return signals