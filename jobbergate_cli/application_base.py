import yaml

class JobbergateApplicationBase(object):
    def __init__(self):
        jobbergate_yaml_file = open("/tmp/jobbergate.yaml")
        jobbergate_yaml = yaml.load(jobbergate_yaml_file, Loader=yaml.FullLoader)
        # print(len(jobbergate_yaml))
        self._questions = list()
        self.jobbergate_config = jobbergate_yaml['jobbergate_config']
        self.application_config = jobbergate_yaml['application_config']

    def mainflow(self):
        raise Exception("Inheriting class must override this method.")

    def render(self):
        raise Exception("Inheriting class must override this method.")