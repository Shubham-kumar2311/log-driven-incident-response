from processors.validator import Validator
from processors.enricher import Enricher
from processors.normalizer import Normalizer
from processors.feature_extractor import FeatureExtractor


class ProcessingPipeline:

    def __init__(self):

        self.steps = [
            Validator(),
            Enricher(),
            Normalizer(),
            FeatureExtractor()
        ]

    def process(self, event):

        for step in self.steps:

            event = step.process(event)

            if event is None:
                return None

        return event