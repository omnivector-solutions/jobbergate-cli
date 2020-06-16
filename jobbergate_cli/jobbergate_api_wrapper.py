#!/usr/bin/env python3
import os
import requests

JOBBERGATE_API_ENDPOINT = "http://0.0.0.0:8000"

class JobbergateApi:

    def __init__(self, token=None):

        #self.jobbergate_api_url = os.environ['JOBBERGATE_API_URL'].rstrip("/")
        self.token = token
        print(f"self.token is {self.token}")
        self.headers = f"Authorization: Bearer {self.token}"

    def jobbergate_request(self):
        pass

    # Job Scripts
    def list_job_scripts(self):
        pass

    def create_job_script(self, job_script_name, application_id):
        pass

    def get_job_script(self, job_script_id):
        pass

    def update_job_script(self, job_script_id):
        pass

    def delete_job_script(self, job_script_id):
        pass

    # Job Submissions
    def list_job_submissions(self):
        pass

    def create_job_submission(self, job_submission_name, job_script_id):
        pass

    def get_job_submission(self, job_submission_id):
        pass

    def update_job_submission(self, job_submission_id):
        pass

    def delete_job_submission(self, job_submission_id):
        pass

    # Applications
    def list_applications(self):
        application_list = requests.get(
            f"{JOBBERGATE_API_ENDPOINT}/application/",
            auth=("skeef", "skeef25"))
        # test_str = f"application_list.text is {application_list.text}"
        return application_list
        # pass

    def create_application(self, application_name):
        pass

    def get_application(self, application_id):
        pass

    def update_application(self, application_id):
        pass

    def delete_application(self, application_id):
        pass
