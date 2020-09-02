#!/usr/bin/env python3
import os
import json
import importlib
import pathlib
import yaml
import inquirer
from subprocess import Popen, PIPE


import requests
import tarfile

from tabulate import tabulate

from jobbergate_cli.jobbergate_common import (
    JOBBERGATE_APPLICATION_MODULE_PATH,
    JOBBERGATE_APPLICATION_CONFIG_PATH,
    JOBBERGATE_APPLICATION_MODULE_FILE_NAME,
    JOBBERGATE_APPLICATION_CONFIG_FILE_NAME,
    JOBBERGATE_CACHE_DIR,
    TAR_NAME
)


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
        # Suppress from list- and create- application:
        self.application_suppress = [
            'application_config',
            'application_file',
            'created_at',
            'updated_at',
            'application_dir_listing',
            'application_location',
            'application_dir_listing_acquired'
        ]
        self.job_script_suppress = [
            'created_at',
            'updated_at',
            'job_script_data_as_string'
        ]
        self.job_submission_suppress = ['created_at', 'updated_at']

    def tardir(self,
               path,
               tar_name,
               tar_list):
        archive = tarfile.open(tar_name, "w|gz")
        for root, dirs, files in os.walk(path):
            if root in tar_list:
                for file in files:
                    if "templates" in root:
                        archive.add(
                            os.path.join(root, file),
                            arcname=f"/tenplates/{file}"
                        )
                    else:
                        archive.add(
                            os.path.join(root, file),
                            arcname=file
                            )
        archive.close()

    def jobbergate_request(self,
                           method,
                           endpoint,
                           data=None,
                           files=None):
        if method == "GET":
            response = requests.get(
                endpoint,
                headers={'Authorization': 'JWT ' + self.token},
                verify=False)
        if method == "PUT":
            try:
                response = requests.put(
                    endpoint,
                    data=data,
                    files=files,
                    headers={'Authorization': 'JWT ' + self.token},
                    verify=False).json()
            except Exception as e:
                response = "PUT request failed"
                return response

        if method == "DELETE":
            response = requests.delete(
                endpoint,
                headers={'Authorization': 'JWT ' + self.token},
                verify=False)

        if method == "POST":
            try:
                response = requests.post(
                    endpoint,
                    data=data,
                    files=files,
                    headers={'Authorization': 'JWT ' + self.token},
                    verify=False).json()
            except Exception as e:
                response = "POST request failed"
                return response
        return response

    def jobbergate_run(self, *argv):
        cmd = ["/snap/bin/sbatch", "application.sh"]
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
            # error response
            elif type(response) == str:
                tabulate_response = response

            return tabulate_response
        return wrapper

    def import_jobbergate_application_module_into_jobbergate_cli(self):
        spec = importlib.util.spec_from_file_location(
            "JobbergateApplication",
            JOBBERGATE_APPLICATION_MODULE_PATH

        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def assemble_questions(self, questions, question_list):
        '''
        questions: passed in from application.py
        questions_list is list of questions assembled,
        this will be passed into inquirer.prompt for user to answer
        '''
        for i in range(len(questions)):
            try:
                questions[i].default
            except NameError:
                questions[i].default = None

            if questions[i].__class__.__name__ == 'List':
                question = inquirer.List(
                    name=questions[i].variablename,
                    message=questions[i].message,
                    choices=questions[i].choices,
                    default=questions[i].default
                )
            elif questions[i].__class__.__name__ == 'Checkbox':
                question = inquirer.Checkbox(
                    name=questions[i].variablename,
                    message=questions[i].message,
                    choices=questions[i].choices,
                    default=questions[i].default
                )
            elif questions[i].__class__.__name__ == 'Confirm':
                question = inquirer.List(
                    name=questions[i].variablename,
                    message=questions[i].message,
                    choices=["y", "N"],
                    default=questions[i].default
                )
            else:
                question = inquirer.Text(
                    name=questions[i].variablename,
                    message=questions[i].message, )
            question_list.append(question)

        return question_list

    def error_handle(self, error, solution):
        response = {
            "error": error,
            "solution": solution
        }
        return response

    def application_error_check(self, application_path):
        error_check = []

        # check for required files
        local_jobbergate_application_dir = pathlib.Path(application_path)
        local_jobbergate_application_module = \
            local_jobbergate_application_dir / \
            JOBBERGATE_APPLICATION_MODULE_FILE_NAME
        local_jobbergate_application_config = \
            local_jobbergate_application_dir / \
            JOBBERGATE_APPLICATION_CONFIG_FILE_NAME

        if not local_jobbergate_application_dir.exists():
            check = self.error_handle(
                error="invalid application path supplied",
                solution=f"{application_path} is invalid, please review and try again"
            )
            error_check.append(check)
        if not local_jobbergate_application_module.exists():
            check = self.error_handle(
                error=f"Could not find {JOBBERGATE_APPLICATION_MODULE_FILE_NAME} in {application_path}",
                solution=f"Please ensure {JOBBERGATE_APPLICATION_MODULE_FILE_NAME} is in application path provided"
            )
            error_check.append(check)
        if not local_jobbergate_application_config.exists():
            check = self.error_handle(
                error=f"Could not find {JOBBERGATE_APPLICATION_CONFIG_FILE_NAME} in {application_path}",
                solution=f"Please ensure {JOBBERGATE_APPLICATION_CONFIG_FILE_NAME} is in application path provided"
            )
            error_check.append(check)

        return error_check


    # Job Scripts
    @tabulate_decorator
    def list_job_scripts(self, all):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-script/"
        )
        if response.status_code == 200:
            response = response.json()
        else:
            response = self.error_handle(
                error=f"Failed to retrieve job script list",
                solution="Please check credentials or report server error"
            )
            return response
        try:
            response = [
                {k: v for k, v in d.items() if k not in self.job_script_suppress}
                for d in response
        ]
        except:
            #TODO: see note on list-application
            response = "list-job-script failed to retrieve list"

        if all:
            return response
        else:
            response = [d for d in response if d['job_script_owner'] == self.user_id]
            return response

    @tabulate_decorator
    def create_job_script(self,
                          job_script_name,
                          application_id,
                          param_file,
                          debug):

        if application_id is None:
            response = self.error_handle(
                error="--application-id for the job script not defined",
                solution="Please try again with --application-id specified"
            )
            return response

        if job_script_name is None:
            response = self.error_handle(
                error="--name for the job script not defined",
                solution="Please try again with --name specified"
            )
            return response

        data = self.job_script_config
        data['job_script_name'] = job_script_name
        data['application'] = application_id
        data['job_script_owner'] = self.user_id

        if param_file:
            is_param_file = os.path.isfile(param_file)
            if is_param_file is False:
                response = self.error_handle(
                    error=f"invalid --parameter-file supplied, could not find: {param_file}",
                    solution="Please provide the full path to a valid parameter file"
                )
                return response

            files = {'upload_file': open(param_file, 'rb')}

            response = self.jobbergate_request(
                method="POST",
                endpoint=f"{self.api_endpoint}/job-script/",
                data=data,
                files=files
            )

            try:
                rendered_dict = json.loads(response['job_script_data_as_string'])
            except:
                response = self.error_handle(
                    error="could not load job_script_data_as_string from response",
                    solution=f"Please review response: {response}"
                )
                return response

            job_script_data_as_string = ""
            for key, value in rendered_dict.items():
                job_script_data_as_string += "\nNEW_FILE\n"
                job_script_data_as_string += value

            response['job_script_data_as_string'] = job_script_data_as_string

        else:
            app_data = self.jobbergate_request(
                method="GET",
                endpoint=f"{self.api_endpoint}/application/{application_id}"
            )
            if app_data.status_code != 200:
                response = self.error_handle(
                    error=f"invalid --application-id provided, could not find: {application_id}",
                    solution=f"Please confirm application id {application_id} exists and try again"
                )
                return response
            else:
                app_data = app_data.json()

            # Get the jobbergate application python module
            JOBBERGATE_APPLICATION_MODULE_PATH.write_text(
                app_data['application_file']
            )
            # Get the jobbergate application yaml config
            JOBBERGATE_APPLICATION_CONFIG_PATH.write_text(
                app_data['application_config']
            )

            # Load the jobbergate yaml
            with open(JOBBERGATE_APPLICATION_CONFIG_PATH) as file:
                param_dict = yaml.load(
                    file,
                    Loader=yaml.FullLoader
                )

            # Exec the jobbergate application python module
            module = self.import_jobbergate_application_module_into_jobbergate_cli()
            application = module.JobbergateApplication(param_dict)

            # Begin question assembly
            question_list = []
            question_list = self.assemble_questions(
                questions=application._questions,
                question_list=question_list
            )
            answers = inquirer.prompt(question_list)
            param_dict['jobbergate_config'].update(answers)

            if hasattr(application, "shared"):
                shared_questions = application.shared(
                    data=param_dict['jobbergate_config']
                )

                questions_2 = []

                questions_shared = self.assemble_questions(
                    questions=shared_questions,
                    question_list=questions_2
                )

                shared_answers = inquirer.prompt(questions_shared)
                param_dict['jobbergate_config'].update(shared_answers)
            param_filename = f"/{JOBBERGATE_CACHE_DIR}/param_dict.json"
            param_file = open(param_filename, 'w')
            json.dump(param_dict, param_file)
            param_file.close()

            # TODO: Put below in function after testing - DRY
            files = {'upload_file': open(param_filename, 'rb')}

            response = self.jobbergate_request(
                method="POST",
                endpoint=f"{self.api_endpoint}/job-script/",
                data=data,
                files=files
            )

            try:
                rendered_dict = json.loads(response['job_script_data_as_string'])
            except:
                print(response)

            job_script_data_as_string = ""
            for key, value in rendered_dict.items():
                job_script_data_as_string += "\n\nNEW_FILE\n\n"
                job_script_data_as_string += value

            response['job_script_data_as_string'] = job_script_data_as_string

        if debug is False:
            del response['job_script_data_as_string']

        return response

    @tabulate_decorator
    def get_job_script(self,
                       job_script_id,
                       as_str):
        if job_script_id is None:
            response = self.error_handle(
                error="--id not define",
                solution="Please try again with --id specified"
            )
            return response

        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-script/{job_script_id}"
        )
        if response.status_code == 404:
            response = self.error_handle(
                error=f"Could not find job script with id: {job_script_id}",
                solution="Please confirm the is for the job script and try again"
            )
            return response
        else:
            response = response.json()

        rendered_dict = json.loads(response['job_script_data_as_string'])
        if as_str:
            return rendered_dict["application.sh"]
        else:
            job_script_data_as_string = ""
            for key, value in rendered_dict.items():
                job_script_data_as_string += "\nNEW_FILE\n"
                job_script_data_as_string += value

            response['job_script_data_as_string'] = job_script_data_as_string

            return response

    @tabulate_decorator
    def update_job_script(self,
                          job_script_id,
                          job_script_data_as_string):
        if job_script_id is None:
            response = self.error_handle(
                error="--id not defined",
                solution="Please try again with --id specified"
            )
            return response
        if job_script_data_as_string is None:
            response = self.error_handle(
                error="--job-script not defined",
                solution=f"Please provide job script data for updating job script ID: {job_script_id}"
            )
            return response

        data = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-script/{job_script_id}"
        )
        if data.status_code == 200:
            data = data.json()
        else:
            response = self.error_handle(
                error=f"Failed to retrieve job script {job_script_id}",
                solution="Please confirm job submission exists and try again"
            )
            return response
        data['job_script_data_as_string'] = job_script_data_as_string
        print(data)
        response = self.jobbergate_request(
            method="PUT",
            endpoint=f"{self.api_endpoint}/job-script/{job_script_id}/",
            data=data
        )

        return response

    @tabulate_decorator
    def delete_job_script(self,
                          job_script_id):
        if job_script_id is None:
            response = self.error_handle(
                error="--id not defined",
                solution="Please try again with --job-script-id specified"
            )
            return response

        response = self.jobbergate_request(
            method="DELETE",
            endpoint=f"{self.api_endpoint}/job-script/{job_script_id}"
        )
        if response.status_code == 404:
            response = self.error_handle(
                error=f"Failed to DELETE job script id: {job_script_id}",
                solution="Please try again with a valid job script id"
            )
            return response
        else:
            response = response.text

        return response

    # Job Submissions
    @tabulate_decorator
    def list_job_submissions(self, all):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-submission/"
        )
        if response.status_code == 200:
            response = response.json()
        else:
            response = self.error_handle(
                error=f"Failed to retrieve job submission list",
                solution="Please check credentials or report server error"
            )
            return response
        try:
            response = [
                {k: v for k, v in d.items() if k not in self.job_submission_suppress}
                for d in response
            ]
        except:
            #TODO: see note on list-application
            response = "list-job-submission failed to retrieve list"

        if all:
            return response
        else:
            response = [d for d in response if d['job_submission_owner'] == self.user_id]
            return response

    @tabulate_decorator
    def create_job_submission(self,
                              job_script_id,
                              render_only,
                              job_submission_name=""):
        if job_script_id is None:
            response = self.error_handle(
                error="--job-script-id not defined",
                solution="Please try again with --job-script-id specified"
            )
            return response

        data = self.job_submission_config
        data['job_submission_name'] = job_submission_name
        data['job_script'] = job_script_id
        data['job_submission_owner'] = self.user_id

        job_script = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-script/{job_script_id}"
        )
        if job_script.status_code == 200:
            job_script = job_script.json()
        else:
            response = self.error_handle(
                error=f"Failed to retrieve job script id={job_script_id}",
                solution="Please confirm job script exists and try job submission again"
            )
            return response

        application_id = job_script['application']

        application = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/application/{application_id}"
        )
        if application.status_code == 200:
            application = application.json()
        else:
            response = self.error_handle(
                error=f"Failed to retrieve the application id={application_id}linked to job script id={job_script_id}",
                solution="Please confirm application exists and try job submission again"
            )
            return response

        application_name = application['application_name']

        rendered_dict = json.loads(
            job_script['job_script_data_as_string']
        )

        for key, value in rendered_dict.items():
            write_file = open(key, 'w')
            write_file.write(value)
            write_file.close()

        if render_only:
            response = self.jobbergate_request(
                method="POST",
                endpoint=f"{self.api_endpoint}/job-submission/",
                data=data
            )
        else:
            try:
                output, err, rc = self.jobbergate_run(application_name)
            except FileNotFoundError:
                response = self.error_handle(
                    error=f"Failed to execute submission",
                    solution="Please confirm slurm sbatch is installed and available"
                )
                return response

            if rc == 0:
                print(output)
                find = output.find("job") + 4
                slurm_job_id = output[find:]
                data['slurm_job_id'] = slurm_job_id
                response = self.jobbergate_request(
                    method="POST",
                    endpoint=f"{self.api_endpoint}/job-submission/",
                    data=data
                )
            else:
                response = self.error_handle(
                    error=f"Failed to execute submission with error: {err}",
                    solution="Please resolve error or contact for assistance"
                )
                return response
        return response

    @tabulate_decorator
    def get_job_submission(self,
                           job_submission_id):
        if job_submission_id is None:
            response = self.error_handle(
                error="--id not defined",
                solution="Please try again with --id specified"
            )
            return response

        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-submission/{job_submission_id}"
        )
        if response.status_code == 404:
            response = self.error_handle(
                error=f"Could not find job submission with id: {job_submission_id}",
                solution="Please confirm the is for the job submission and try again"
            )
            return response
        else:
            response = response.json()

        return response

    @tabulate_decorator
    def update_job_submission(self,
                              job_submission_id):
        if job_submission_id is None:
            response = self.error_handle(
                error="--id not defined",
                solution="Please try again with --id specified"
            )
            return response

        data = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/job-submission/{job_submission_id}"
        )
        if data.status_code == 200:
            data = data.json()
        else:
            response = self.error_handle(
                error=f"Failed to retrieve job submission {job_submission_id}",
                solution="Please confirm job submission exists and try again"
            )
            return response
        # TODO how to collect data that will updated for the job-submission
        response = self.jobbergate_request(
            method="PUT",
            endpoint=f"{self.api_endpoint}/job-submission/{job_submission_id}/"
        )
        return response

    @tabulate_decorator
    def delete_job_submission(self,
                              job_submission_id):
        if job_submission_id is None:
            response = self.error_handle(
                error="--id not defined",
                solution="Please try again with --id specified"
            )
            return response


        response = self.jobbergate_request(
            method="DELETE",
            endpoint=f"{self.api_endpoint}/job-submission/{job_submission_id}"
        )
        if response.status_code == 404:
            response = self.error_handle(
                error=f"Failed to DELETE job submission id: {job_submission_id}",
                solution="Please try again with a valid job submission id"
            )
            return response
        else:
            response = response.text

        return response

    # Applications
    @tabulate_decorator
    def list_applications(self, all):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/application/"
        )
        if response.status_code == 200:
            response = response.json()
        else:
            response = self.error_handle(
                error=f"Failed retrieve application list",
                solution="Please try credentials again or server error"
            )
            return response

        try:
            response = [
                {k: v for k, v in d.items() if k not in self.application_suppress}
                for d in response
            ]
        except:
            # TODO:I think this would only error on an auth issue handled elsewhere - should think through more
            response = "list-applications failed to retrieve list"

        if all:
            return response
        else:
            response = [d for d in response if d['application_owner'] == self.user_id]
            return response


    @tabulate_decorator
    def create_application(self,
                           application_name,
                           application_path,
                           application_desc):
        '''
        create an application based on path provided by the user
        '''
        parameter_check = []
        if application_name is None:
            response = self.error_handle(
                error="--name not defined",
                solution="Please try again with --name specified for the application"
            )
            parameter_check.append(response)

        if application_path is None:
            response = self.error_handle(
                error="--application-path not defined",
                solution="Please try again with --application-path specified for the application"
            )
            parameter_check.append(response)
        if len(parameter_check) > 0:
            response = parameter_check
            return response

        error_check = self.application_error_check(application_path)

        if len(error_check) > 0:
            response = error_check
            return response


        data = self.application_config
        data['application_name'] = application_name
        data['application_owner'] = self.user_id

        if application_desc:
            data['application_description'] = application_desc

        tar_list = [application_path, os.path.join(application_path, "templates")]
        self.tardir(application_path, TAR_NAME, tar_list)

        files = {'upload_file': open(TAR_NAME, 'rb')}

        response = self.jobbergate_request(
            method="POST",
            endpoint=f"{self.api_endpoint}/application/",
            data=data,
            files=files
        )

        try:
            for key in self.application_suppress:
                response.pop(key, None)
        except AttributeError:
            # response is str of error message
            return response

        print(var_does_not_exist)
        os.remove(TAR_NAME)

        return response

    @tabulate_decorator
    def get_application(self,
                        application_id):
        response = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/application/{application_id}"
        )

        if response.status_code == 404:
            response = self.error_handle(
                error=f"Could not find application with id: {application_id}",
                solution="Please confirm the is for the application and try again"
            )
            return response
        else:
            response = response.json()

        return response

    @tabulate_decorator
    def update_application(self,
                           application_id,
                           application_path,
                           application_desc
                           ):
        if application_path is None:
            response = self.error_handle(
                error="--application-path not defined",
                solution="Please try again with --application-path specified"
            )
            return response

        error_check = self.application_error_check(application_path)

        if len(error_check) > 0:
            response = error_check
            return response

        data = self.jobbergate_request(
            method="GET",
            endpoint=f"{self.api_endpoint}/application/{application_id}"
        )
        if data.status_code == 200:
            data = data.json()
        else:
            response = self.error_handle(
                error=f"Application id {application_id} does not exist",
                solution="Please confirm the application id"
            )
            return response

        del data['id']
        del data['created_at']
        del data['updated_at']
        if application_desc:
            data['application_description'] = application_desc

        tar_list = [application_path, os.path.join(application_path, "templates")]
        self.tardir(application_path, TAR_NAME, tar_list)

        files = {'upload_file': open(TAR_NAME, 'rb')}

        response = self.jobbergate_request(
            method="PUT",
            endpoint=f"{self.api_endpoint}/application/{application_id}/",
            data=data,
            files=files
        )

        try:
            for key in self.application_suppress:
                response.pop(key, None)

            os.remove(TAR_NAME)
        except AttributeError:
            # response is str of error message
            return response
        return response

    @tabulate_decorator
    def delete_application(self,
                           application_id):
        response = self.jobbergate_request(
            method="DELETE",
            endpoint=f"{self.api_endpoint}/application/{application_id}"
        )
        if response.status_code == 404:
            response = self.error_handle(
                error=f"Failed to DELETE job submission id: {application_id}",
                solution="Please try again with a valid job submission id"
            )
            return response
        else:
            response = response.text

        return response
