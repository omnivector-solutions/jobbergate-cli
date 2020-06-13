#!/usr/bin/env python3
import requests
import sys

from requests.auth import HTTPBasicAuth


class JobbergateApi:

    def __init__(self, username=None, password=None, token=None):

        self.jobbergate_api_url = os.environ['JOBBERGATE_API_URL'].rstrip("/")

        if not (username and password) or not token:
            print("Need to supply a jwt, or username + password")
            sys.exit()
        else:
            if (username and password):
                self._get_jwt_from_api({
                    'username': username,
                    'password': password
                })
            else:
                self.token = token

    def _get_jwt_from_api(self, data): 
        resp = requests.get(
            f"{self.jobbergate_api_url}/get-token",
            auth=(data['username', data['password'],
        )
        self.token = resp['token']

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
        pass

    def create_application(self, application_name):
        pass

    def get_application(self, application_id):
        pass

    def update_application(self, application_id):
        pass

    def delete_application(self, application_id):
        pass
