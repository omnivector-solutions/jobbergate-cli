import yaml

class JobbergateApplicationBase:
    def __init__(self):
        jobbergate_yaml = yaml.load("jobbergate.yaml")
        self._questions = list()
        self.jobbergate_config = jobbergate_yaml['jobbergate-config']
        self.application_config = jobbergate_yaml['application-config']

    def mainflow(self):
        raise Exception("Inheriting class must override this method.")

    def render(self):
        raise Exception("Inheriting class must override this method.")