#!/usr/bin/env python3
import os
import json
import requests

JOBBERGATE_API_ENDPOINT = "http://0.0.0.0:8000"

class JobbergateApi:

    def __init__(self, token=None):

        #self.jobbergate_api_url = os.environ['JOBBERGATE_API_URL'].rstrip("/")
        self.token = token

    def jobbergate_request(self):
        pass

    # Job Scripts
    def list_job_scripts(self):
        jobscript_list = requests.get(
            f"{JOBBERGATE_API_ENDPOINT}/job-script/",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return jobscript_list

    def create_job_script(self, job_script_name, application_id):
        f = open('config/jobsubmission.json', "r")
        data = json.loads(f.read())
        data['job_script_name'] = job_script_name
        data['application'] = application_id
        resp = requests.post(
            f"{JOBBERGATE_API_ENDPOINT}/job-submission/",
            data=data,
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return resp

    def get_job_script(self, job_script_id):
        resp = requests.get(
            f"{JOBBERGATE_API_ENDPOINT}/job-script/{job_script_id}",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return resp

    def update_job_script(self, job_script_id):
        f = open('config/application.json', "r")
        data = json.loads(f.read())
        # data['job_script_name'] = job_script_name
        #TODO how to collect data that will update the job-script
        resp = requests.put(
            f"{JOBBERGATE_API_ENDPOINT}/job-script/{job_script_id}",
            data=data,
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return resp

    def delete_job_script(self, job_script_id):
        resp = requests.delete(
            f"{JOBBERGATE_API_ENDPOINT}/job-script/{job_script_id}",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return resp

    # Job Submissions
    def list_job_submissions(self):
        jobsubmission_list = requests.get(
            f"{JOBBERGATE_API_ENDPOINT}/job-submission/",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return jobsubmission_list

    def create_job_submission(self, job_submission_name, job_script_id):
        f = open('config/jobsubmission.json', "r")
        data = json.loads(f.read())
        data['job_submission_name'] = job_submission_name
        data['job_script'] = job_script_id
        resp = requests.post(
            f"{JOBBERGATE_API_ENDPOINT}/job-submission/",
            data=data,
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return resp

    def get_job_submission(self, job_submission_id):
        resp = requests.get(
            f"{JOBBERGATE_API_ENDPOINT}/job-submission/{job_submission_id}",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return resp

    def update_job_submission(self, job_submission_id):
        f = open('config/application.json', "r")
        data = json.loads(f.read())
        # TODO how to collect data that will update the job-script
        resp = requests.put(
            f"{JOBBERGATE_API_ENDPOINT}/job-submission/{job_submission_id}",
            data=data,
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return resp

    def delete_job_submission(self, job_submission_id):
        resp = requests.delete(
            f"{JOBBERGATE_API_ENDPOINT}/job-submission/{job_submission_id}",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return resp

    # Applications
    def list_applications(self):
        application_list = requests.get(
            f"{JOBBERGATE_API_ENDPOINT}/application/",
            # auth=("skeef", "skeef25"),
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return application_list

    def create_application(self, application_name):
        f = open('config/application.json', "r")
        data = json.loads(f.read())
        data['application_name'] = application_name
        resp = requests.post(
            f"{JOBBERGATE_API_ENDPOINT}/application/",
            data=data,
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return resp

    def get_application(self, application_id):
        resp = requests.get(
            f"{JOBBERGATE_API_ENDPOINT}/application/{application_id}",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return resp

    def update_application(self, application_id):
        f = open('config/application.json', "r")
        data = json.loads(f.read())
        data['application_name'] = "TEST_NEW_APP_NAME10"
        resp = requests.put(
            f"{JOBBERGATE_API_ENDPOINT}/application/{application_id}",
            data=data,
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return resp

    def delete_application(self, application_id):
        resp = requests.delete(
            f"{JOBBERGATE_API_ENDPOINT}/application/{application_id}",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return resp
