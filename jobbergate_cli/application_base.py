#!/usr/bin/python3
"""ApplicationBase."""


class JobbergateApplicationBase:
    """JobbergateApplicationBase."""

    def __init__(self, jobbergate_yaml):
        """Initialize class attributes."""
        self._questions = []
        self.jobbergate_config = jobbergate_yaml['jobbergate_config']
        self.application_config = jobbergate_yaml['application_config']
        self.mainflow()

    def mainflow(self):
        """Implements the main question asking workflow."""
        raise Exception("Inheriting class must override this method.")
