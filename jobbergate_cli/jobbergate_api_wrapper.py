#!/usr/bin/env python3
import os
import json

from subprocess import Popen, PIPE
import requests
import tarfile

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

    def tardir(self, path, tar_name):
        archive = tarfile.open(tar_name, "w|gz")
        for root, dirs, files in os.walk(path):
            for file in files:
                archive.add(
                    os.path.join(root, file),
                    arcname=file
                    )
        archive.close()

    def jobbergate_request(self, method, endpoint, data=None, files=None):
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
                files=files,
                headers={'Authorization': 'JWT ' + self.token},
                verify=False).json()
        return response

    def jobbergate_run(self, application_name, *argv):
        # cmd = ["slurm.sbatch", "-p", "partition1", "application.sh"]
        cmd = ["slurm.sbatch", "application.sh"]
        for arg in argv:
            cmd.append(arg)
        p = Popen(
            cmd,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE)
        output, err = p.communicate(b"sbatch output")

        rc = p.returncode

        return output.decode("utf-8"), err.decode("utf-8"), rc

    def tabulate_decorator(func):
        def wrapper(*args, **kwargs):
            # getting the returned value
            response = func(*args, **kwargs)
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
        return wrapper

    # Job Scripts
    @tabulate_decorator
    def list_job_scripts(self):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-script/"
        )
        response = [{k: v for k, v in d.items() if k != 'job_script_data_as_string'} for d in response]
        return response

    @tabulate_decorator
    def create_job_script(self, job_script_name, application_id, param_file):
        data = self.job_script_config
        data['job_script_name'] = job_script_name
        data['application'] = application_id
        data['job_script_owner'] = self.user_id

        files = {'upload_file': open(param_file, 'rb')}

        response = self.jobbergate_request(
            method="POST",
            endpoint=f"{self.api_endpoint}/job-script/",
            data=data,
            files=files
        )

        rendered_dict = json.loads(response['job_script_data_as_string'])

        job_script_data_as_string = ""
        for key, value in rendered_dict.items():
            job_script_data_as_string += "\nNEW_FILE\n"
            job_script_data_as_string += value

        response['job_script_data_as_string'] = job_script_data_as_string

        return response

    @tabulate_decorator
    def get_job_script(self, job_script_id):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-script/{job_script_id}"
        )

        rendered_dict = json.loads(response['job_script_data_as_string'])

        job_script_data_as_string = ""
        for key, value in rendered_dict.items():
            job_script_data_as_string += "\nNEW_FILE\n"
            job_script_data_as_string += value

        response['job_script_data_as_string'] = job_script_data_as_string

        return response

    @tabulate_decorator
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

        return response

    def delete_job_script(self, job_script_id):
        response = self.jobbergate_request(
            method="DELETE",
            endpoint=f"{self.api_endpoint}/job-script/{job_script_id}"
        )
        return response

    # Job Submissions
    @tabulate_decorator
    def list_job_submissions(self):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-submission/"
        )
        return response

    @tabulate_decorator
    def create_job_submission(self, job_submission_name, job_script_id):
        data = self.job_submission_config
        data['job_submission_name'] = job_submission_name
        data['job_script'] = job_script_id
        data['job_submission_owner'] = self.user_id

        job_script = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-script/{job_script_id}"
        )

        application_id = job_script['application']

        application = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/application/{application_id}"
        )

        application_name = application['application_name']

        rendered_dict = json.loads(job_script['job_script_data_as_string'])

        for key, value in rendered_dict.items():
            write_file = open(key, 'w')
            write_file.write(value)
            write_file.close()

        output, err, rc = self.jobbergate_run(application_name)

        print(f"output: {output}")
        print(f"err: {err}")

        response = self.jobbergate_request(
            method="POST",
            endpoint=f"{self.api_endpoint}/job-submission/",
            data=data
        )
        return response

    @tabulate_decorator
    def get_job_submission(self, job_submission_id):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-submission/{job_submission_id}"
        )

        return response

    @tabulate_decorator
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
        return response

    def delete_job_submission(self, job_submission_id):
        response = self.jobbergate_request(
            method="DELETE",
            endpoint=f"{self.api_endpoint}/job-submission/{job_submission_id}"
        )
        return response

    # Applications
    @tabulate_decorator
    def list_applications(self):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/application/"
        )
        return response

    @tabulate_decorator
    def create_application(self, application_name, application_path, base_path):
        '''
        create an application based on path provided by the user
        '''

        data = self.application_config
        data['application_name'] = application_name
        data['application_owner'] = self.user_id

        tar_name = "application.tar.gz"
        s3_key = f"{base_path}/{str(self.user_id)}/{application_name}/application_id/{tar_name}"
        data['application_location'] = s3_key

        self.tardir(application_path, tar_name)

        files = {'upload_file': open(tar_name, 'rb')}

        response = self.jobbergate_request(
            method="POST",
            endpoint=f"{self.api_endpoint}/application/",
            data=data,
            files=files
        )

        return response

    @tabulate_decorator
    def get_application(self, application_id):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/application/{application_id}"
        )

        return response

    @tabulate_decorator
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
        return response

    def delete_application(self, application_id):
        response = self.jobbergate_request(
            method="DELETE",
            endpoint=f"{self.api_endpoint}/application/{application_id}"
        )

        return response
