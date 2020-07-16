#!/usr/bin/env python3
import os
from subprocess import Popen, PIPE
import json
import requests
import tarfile

import boto3
from tabulate import tabulate

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
        self.bucket = boto3.resource('s3').Bucket('omnivector-misc')

    def jobbergate_request(self):
        pass

    def tardir(self, path, tar_name):
        with tarfile.open(tar_name, "w:gz") as tar_handle:
            for root, dirs, files in os.walk(path):
                for file in files:
                    tar_handle.add(os.path.join(root, file))

    def jobbergate_request(self, method, endpoint, data=None):
        if method == "GET":
            response = requests.get(
                endpoint,
                headers={'Authorization': 'JWT ' + self.token},
                verify=False).json()
        if method == "PUT":
            response = requests.put(
                endpoint,
                data=data,
                headers={'Authorization': 'JWT ' + self.token},
                verify=False).json()
        if method == "DELETE":
            response = requests.delete(
                endpoint,
                headers={'Authorization': 'JWT ' + self.token},
                verify=False).text
        if method == "POST":
            response = requests.post(
                endpoint,
                data=data,
                headers={'Authorization': 'JWT ' + self.token},
                verify=False).json()
        return response

    def jobbergate_run(self, application_name, *argv):
        cmd = ["sbatch", "-p", "partition1", f"{application_name}.sh"]
        for arg in argv:
            cmd.append(arg)
        print(cmd)
        p = Popen(
            cmd,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE)
        output, err = p.communicate(b"sbatch output")

        rc = p.returncode
        print(f"output: {output}")
        print(f"err: {err}")
        print(rc)

        return output, err, rc


    def tabulate_response(self, response):
        if type(response) == list:
            tabulate_response = tabulate(
                (my_dict for my_dict in response),
                headers="keys"
            )
        elif type(response) == dict:
            tabulate_response = tabulate(
                response.items()
            )

        return tabulate_response

    # Job Scripts
    def list_job_scripts(self):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-script/"
        )
        response_formatted = self.tabulate_response(response)
        return response_formatted

    def create_job_script(self, job_script_name, application_id):
        data = self.job_script_config
        data['job_script_name'] = job_script_name
        data['application'] = application_id
        data['job_script_owner'] = self.user_id

        response = self.jobbergate_request(
            method="POST",
            endpoint=f"{self.api_endpoint}/job-script/",
            data=data
        )

        response_formatted = self.tabulate_response(response)

        return response_formatted

    def get_job_script(self, job_script_id):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-script/{job_script_id}"
        )

        response_formatted = self.tabulate_response(response)

        return response_formatted

    def update_job_script(self, job_script_id):
        data = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-script/{job_script_id}"
        )
        data['job_script_name'] = "TEST_NEW_JOBSCRIPT_NAME_CLI"
        response = self.jobbergate_request(
            method="PUT",
            endpoint=f"{self.api_endpoint}/job-script/{job_script_id}/",
            data=data
        )

        response_formatted = self.tabulate_response(response)

        return response_formatted

    def delete_job_script(self, job_script_id):
        response = self.jobbergate_request(
            method="DELETE",
            endpoint=f"{self.api_endpoint}/job-script/{job_script_id}"
        )

        return response

    # Job Submissions
    def list_job_submissions(self):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-submission/"
        )

        response_formatted = self.tabulate_response(response)

        return response_formatted

    def create_job_submission(self, job_submission_name, job_script_id):
        data = self.job_submission_config
        data['job_submission_name'] = job_submission_name
        data['job_script'] = job_script_id
        data['job_submission_owner'] = self.user_id

        job_script = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-script/{job_script_id}"
        )
        print(job_script)

        application_id = job_script['application']

        application = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/application/{application_id}"
        )

        application_location = application['application_location']
        application_name = application['application_name']
        application_filename = application_location.split("/")[-1]

        self.bucket.download_file(application_location, application_filename)

        application_tar = tarfile.open(application_filename)
        for member in application_tar.getmembers():
            if member.isreg():  # skip if the TarInfo is not files
                member.name = os.path.basename(member.name)  # remove the path by reset it
                application_tar.extract(member, ".")  # extract
        application_tar.close()

        #TODO need to work out collecting paramters for job_script based on config

        output, err, rc = self.jobbergate_run(application_name)

        response = self.jobbergate_request(
            method="POST",
            endpoint=f"{self.api_endpoint}/job-submission/",
            data=data
        )

        response_formatted = self.tabulate_response(response)

        return response_formatted, job_script, application

    def get_job_submission(self, job_submission_id):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-submission/{job_submission_id}"
        )

        response_formatted = self.tabulate_response(response)

        return response_formatted

    def update_job_submission(self, job_submission_id):
        data = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-submission/{job_submission_id}"
        )
        # TODO how to collect data that will updated for the job-submission
        data['job_submission_name'] = "TEST_JOB_SUB_CLI"
        response = self.jobbergate_request(
            method="PUT",
            endpoint=f"{self.api_endpoint}/job-submission/{job_submission_id}/"
        )

        response_formatted = self.tabulate_response(response)

        return response_formatted

    def delete_job_submission(self, job_submission_id):
        response = self.jobbergate_request(
            method="DELETE",
            endpoint=f"{self.api_endpoint}/job-submission/{job_submission_id}"
        )

        return response

    # Applications
    def list_applications(self):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/application/"
        )

        response_formatted = self.tabulate_response(response)

        return response_formatted

    def create_application(self, application_name, application_path, base_path):
        data = self.application_config
        data['application_name'] = application_name
        data['application_owner'] = self.user_id

        tar_name = f"{application_name}.tar.gz"

        self.tardir(application_path, tar_name)

        s3_key = f"{base_path}{str(self.user_id)}/{application_name}/{tar_name}"

        self.bucket.upload_file(tar_name, s3_key)
        data['application_location'] = s3_key

        response = self.jobbergate_request(
            method="POST",
            endpoint=f"{self.api_endpoint}/application/",
            data=data
        )

        response_formatted = self.tabulate_response(response)

        return response_formatted

    def get_application(self, application_id):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/application/{application_id}"
        )

        response_formatted = self.tabulate_response(response)

        return response_formatted

    def update_application(self, application_id):
        data = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/application/{application_id}"
        )

        data['application_name'] = "TEST_NEW_APP_NAME10"
        del data['id']
        del data['created_at']
        del data['updated_at']
        response = self.jobbergate_request(
            method="PUT",
            endpoint=f"{self.api_endpoint}/application/{application_id}/",
            data=data
        )

        response_formatted = self.tabulate_response(response)

        return response_formatted

    def delete_application(self, application_id):
        response = self.jobbergate_request(
            method="DELETE",
            endpoint=f"{self.api_endpoint}/application/{application_id}"
        )

        return response
