#!/usr/bin/env python3
import os
import json
import requests
import zipfile

import boto3


class JobbergateApi:

    def __init__(self,
                 token=None,
                 job_script_config=None,
                 job_submission_config=None,
                 application_config=None,
                 api_endpoint=None,
                 user_id=None):

        self.token = token
        self.job_script_config = job_script_config
        self.job_submission_config = job_submission_config
        self.application_config = application_config
        self.api_endpoint = api_endpoint
        self.user_id = user_id

    def jobbergate_request(self):
        pass

    def zipdir(self, zip_path, zip_file):
        # ziph is zipfile handle
        for root, dirs, files in os.walk(zip_path):
            for file in files:
                zip_file.write(os.path.join(root, file))


    # Job Scripts
    def list_job_scripts(self):
        jobscript_list = requests.get(
            f"{self.api_endpoint}/job-script/",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).json()
        return jobscript_list

    def create_job_script(self, job_script_name, application_id):
        f = open(self.job_script_config, "r")
        data = json.loads(f.read())
        data['job_script_name'] = job_script_name
        data['application'] = application_id
        data['job_script_owner'] = self.user_id
        print(f"job script data is {data}")
        resp = requests.post(
            f"{self.api_endpoint}/job-script/",
            data=data,
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).text
        return resp

    def get_job_script(self, job_script_id):
        resp = requests.get(
            f"{self.api_endpoint}/job-script/{job_script_id}",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).json()
        return resp

    def update_job_script(self, job_script_id):
        data = requests.get(
            f"{self.api_endpoint}/job-script/{job_script_id}",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).json()
        data['job_script_name'] = "TEST_NEW_JOBSCRIPT_NAME_CLI"
        #TODO how to collect data that will be updated for the job-script
        resp = requests.put(
            f"{self.api_endpoint}/job-script/{job_script_id}/",
            data=data,
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).text
        return resp

    def delete_job_script(self, job_script_id):
        resp = requests.delete(
            f"{self.api_endpoint}/job-script/{job_script_id}",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).text
        return resp

    # Job Submissions
    def list_job_submissions(self):
        jobsubmission_list = requests.get(
            f"{self.api_endpoint}/job-submission/",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).json()
        return jobsubmission_list

    def create_job_submission(self, job_submission_name, job_script_id):
        f = open(self.job_submission_config, "r")
        data = json.loads(f.read())
        data['job_submission_name'] = job_submission_name
        data['job_script'] = job_script_id
        data['job_submission_owner'] = self.user_id
        resp = requests.post(
            f"{self.api_endpoint}/job-submission/",
            data=data,
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).text
        return resp

    def get_job_submission(self, job_submission_id):
        resp = requests.get(
            f"{self.api_endpoint}/job-submission/{job_submission_id}",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).json()
        return resp

    def update_job_submission(self, job_submission_id):
        data = requests.get(
            f"{self.api_endpoint}/job-submission/{job_submission_id}",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).json()
        # TODO how to collect data that will updated for the job-submission
        data['job_submission_name'] = "TEST_JOB_SUB_CLI"
        resp = requests.put(
            f"{self.api_endpoint}/job-submission/{job_submission_id}/",
            data=data,
            headers={'Authorization': 'JWT ' + self.token},
            verify=False)
        return resp

    def delete_job_submission(self, job_submission_id):
        resp = requests.delete(
            f"{self.api_endpoint}/job-submission/{job_submission_id}",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).text
        return resp

    # Applications
    def list_applications(self):
        application_list = requests.get(
            f"{self.api_endpoint}/application/",
            # auth=("skeef", "skeef25"),
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).json()
        return application_list

    def create_application(self, application_name, application_path):
        f = open(self.application_config, "r")
        data = json.loads(f.read())
        data['application_name'] = application_name
        data['application_owner'] = self.user_id

        # hard code path for now
        tmp_save_path = '/Users/stephenkeefauver/github/TEST/jobberappliation_TEST.zip'
        zip_file = zipfile.ZipFile(tmp_save_path, 'w', zipfile.ZIP_DEFLATED)
        self.zipdir(application_path, zip_file)
        zip_file.close()

        s3 = boto3.resource('s3')
        s3.meta.client.upload_file(tmp_save_path, 'omnivector-misc', 'jobbergate-cli/test_app_upload.zip')

        resp = requests.post(
            f"{self.api_endpoint}/application/",
            data=data,
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).text
        return resp

    def get_application(self, application_id):
        resp = requests.get(
            f"{self.api_endpoint}/application/{application_id}",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).json()
        return resp

    def update_application(self, application_id):
        data = requests.get(
            f"{self.api_endpoint}/application/{application_id}",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).json()
        data['application_name'] = "TEST_NEW_APP_NAME10"
        del data['id']
        del data['created_at']
        del data['updated_at']
        print(f"app data is {data}")
        resp = requests.put(
            f"{self.api_endpoint}/application/{application_id}/",
            data=data,
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).text
        return resp

    def delete_application(self, application_id):
        resp = requests.delete(
            f"{self.api_endpoint}/application/{application_id}",
            headers={'Authorization': 'JWT ' + self.token},
            verify=False).text
        return resp
