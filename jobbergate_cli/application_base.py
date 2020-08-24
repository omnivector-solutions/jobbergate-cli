class JobbergateApplicationBase:
    def __init__(self, jobbergate_yaml):
        self._questions = []
        self.jobbergate_config = jobbergate_yaml['jobbergate_config']
        self.application_config = jobbergate_yaml['application_config']
        self.mainflow()

    def mainflow(self):
        raise Exception("Inheriting class must override this method.")
