#!/usr/bin/python3
import os
"""ApplicationBase."""


class JobbergateApplicationBase:
    """JobbergateApplicationBase."""

    def __init__(self, jobbergate_yaml):
        """Initialize class attributes."""
        self.jobbergate_config = jobbergate_yaml['jobbergate_config']
        self.application_config = jobbergate_yaml['application_config']

    def mainflow(self, data):
        """Implements the main question asking workflow."""
        raise Exception("Inheriting class must override this method.")

    def get_template_files(self):
        templates = [template for root, directory, template in os.walk("./templates")]
        print(f"templates are: {templates}")
        print(os.getcwd())
        return templates[0]
