#!/usr/bin/env python3
import importlib
import json
import os
import pathlib
from subprocess import PIPE, Popen
import tarfile
from urllib.parse import urljoin

import inquirer
import requests
from tabulate import tabulate
import yaml

from jobbergate_cli import appform, client
from jobbergate_cli.jobbergate_common import (
    JOBBERGATE_APPLICATION_CONFIG_FILE_NAME,
    JOBBERGATE_APPLICATION_CONFIG_PATH,
    JOBBERGATE_APPLICATION_MODULE_FILE_NAME,
    JOBBERGATE_APPLICATION_MODULE_PATH,
    JOBBERGATE_CACHE_DIR,
    SBATCH_PATH,
    TAR_NAME,
)


class JobbergateApi:
    def __init__(
        self,
        token=None,
        job_script_config=None,
        job_submission_config=None,
        application_config=None,
        api_endpoint=None,
        user_id=None,
    ):
        """Initialize JobbergateAPI."""

        self.token = token
        self.job_script_config = job_script_config
        self.job_submission_config = job_submission_config
        self.application_config = application_config
        self.api_endpoint = api_endpoint
        self.user_id = user_id
        # Suppress from list- and create- application:
        self.application_suppress = [
            "application_config",
            "application_file",
            "created_at",
            "updated_at",
            "application_dir_listing",
            "application_location",
            "application_dir_listing_acquired",
        ]
        self.job_script_suppress = [
            "created_at",
            "updated_at",
            "job_script_data_as_string",
        ]
        self.job_submission_suppress = ["created_at", "updated_at"]

    def tardir(self, path, tar_name, tar_list):
        """
        Compress application files to a tar file.

        Keyword Arguments:
            path      -- Path provided by user to dir
            tar_name  -- name of tar file
            tar_list  -- list of values for root to be added to tar file
                         this is to avoid including extraneous files in tar

        """
        archive = tarfile.open(tar_name, "w|gz")
        for root, dirs, files in os.walk(path):
            if root in tar_list:
                for file in files:
                    if "templates" in root:
                        archive.add(
                            os.path.join(root, file), arcname=f"/templates/{file}"
                        )
                    else:
                        archive.add(os.path.join(root, file), arcname=file)
        archive.close()

    def jobbergate_request(self, method, endpoint, data=None, files=None):
        """
        Submit HTTP requests.

        Keyword Arguments:
            method    -- HTTP request method
            endpoint  -- API End point: application, job-script, job-submission
            data      -- data to be submitted on POST/PUT requests
            files     -- file(s) to be sent with request where applicable

        """
        if method == "GET":
            try:
                response = client.get(
                    endpoint,
                    headers={"Authorization": "JWT " + self.token},
                    verify=False,
                )
                if response.status_code == 200:
                    response = response.json()
                elif response.status_code == 403:
                    response = self.error_handle(
                        error=f"User is not Authorized to access {endpoint}",
                        solution="Please contact your admin for permission",
                    )
                    return response
                elif response.status_code == 404:
                    response = self.error_handle(
                        error=f"Could not find object at {endpoint}",
                        solution="Please confirm the URL or the id and try again",
                    )
                    return response
                else:
                    response = self.error_handle(
                        error=f"Failed to access {endpoint}",
                        solution="Please check credentials or report server error",
                    )
                    return response

            except requests.exceptions.ConnectionError:
                response = self.error_handle(
                    error="Failed to establish connection with API",
                    solution="Please try submitting again",
                )
                return response
        if method == "PUT":
            try:
                response = client.put(
                    endpoint,
                    data=data,
                    files=files,
                    headers={"Authorization": "JWT " + self.token},
                    verify=False,
                )  # .json()
                if response.status_code == 403:
                    response = self.error_handle(
                        error=f"User is not Authorized to access {endpoint}",
                        solution="Please contact your admin for permission",
                    )
                    return response
                else:
                    response = response.json()
            except Exception:
                response = "PUT request failed"
                return response

        if method == "DELETE":
            response = client.delete(
                endpoint, headers={"Authorization": "JWT " + self.token}, verify=False
            )
            if response.status_code == 403:
                response = self.error_handle(
                    error=f"User is not Authorized to access {endpoint}",
                    solution="Please contact your admin for permission",
                )
                return response
            elif response.status_code == 404:
                response = self.error_handle(
                    error=f"Could not delete object at {endpoint}",
                    solution="Please confirm the id and try again",
                )
                return response
            else:
                response = response.text

        if method == "POST":
            full_response = client.post(
                endpoint,
                data=data,
                files=files,
                headers={"Authorization": "JWT " + self.token},
                verify=False,
            )
            if full_response.status_code == 400:
                response = self.error_handle(
                    error=f"Error with data uploaded: {full_response.text}",
                    solution="Please resolve issue and re submit",
                )
                return response
            elif full_response.status_code == 500:
                error = full_response.text
                start_point = error.find("Exception Type:")
                # shorter error resp:
                end_point = error.find("GET:")
                # Longer error resp:
                # end_point = error.find("COOKIES")
                response = self.error_handle(
                    error=f"Server Error generated: {error[start_point:end_point]}",
                    solution="Please alert Omnivector for resolution",
                )
            elif full_response.status_code == 403:
                response = self.error_handle(
                    error=f"User is not Authorized to access {endpoint}",
                    solution="Please contact your admin for permission",
                )
                return response

            elif full_response.status_code in [200, 201]:
                response = full_response.json()

            else:
                response = self.error_handle(
                    error=f"Unhandled response code from server: {full_response.status_code}",
                    solution="Please alert Omnivector for resolution",
                )

        return response

    def jobbergate_run(self, filename, *argv):
        """Execute Job Submission."""
        cmd = [SBATCH_PATH, filename]
        for arg in argv:
            cmd.append(arg)
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate(b"sbatch output")

        rc = p.returncode

        return output.decode("utf-8"), err.decode("utf-8"), rc

    def tabulate_decorator(func):
        """Decorator to tabulate each response."""

        def wrapper(*args, **kwargs):
            # getting the returned value
            response = func(*args, **kwargs)
            if type(response) == list:
                tabulate_response = tabulate(
                    (my_dict for my_dict in response), headers="keys"
                )
            elif type(response) == dict:
                tabulate_response = tabulate(response.items())
            # error response
            elif type(response) == str:
                tabulate_response = response

            return tabulate_response

        return wrapper

    def import_jobbergate_application_module(self):
        """Import jobbergate.py for generating questions."""
        spec = importlib.util.spec_from_file_location(
            "JobbergateApplication", JOBBERGATE_APPLICATION_MODULE_PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def assemble_questions(self, question, ignore=None):
        """
        Assemble questions from jobbergate.py.

        Keyword Arguments:
            question  -- question object passed in from jobbergate.py.
                         function returns the appropriate question from
                         inquirer
        """

        if isinstance(question, appform.Text):
            return inquirer.Text(
                question.variablename,
                message=question.message,
                default=question.default,
                ignore=ignore,
            )

        if isinstance(question, appform.Integer):
            return inquirer.Text(
                question.variablename,
                message=question.message,
                default=question.default,
                validate=question.validate,
                ignore=ignore,
            )

        if isinstance(question, appform.List):
            return inquirer.List(
                question.variablename,
                message=question.message,
                choices=question.choices,
                default=question.default,
                ignore=ignore,
            )

        if isinstance(question, appform.Directory):
            return inquirer.Path(
                question.variablename,
                message=question.message,
                path_type=inquirer.Path.DIRECTORY,
                default=question.default,
                exists=question.exists,
                ignore=ignore,
            )

        if isinstance(question, appform.File):
            return inquirer.Path(
                question.variablename,
                message=question.message,
                path_type=inquirer.Path.FILE,
                default=question.default,
                exists=question.exists,
                ignore=ignore,
            )

        if isinstance(question, appform.Checkbox):
            return inquirer.Checkbox(
                question.variablename,
                message=question.message,
                choices=question.choices,
                default=question.default,
                ignore=ignore,
            )

        if isinstance(question, appform.Confirm):
            return inquirer.Confirm(
                question.variablename,
                message=question.message,
                default=question.default,
                ignore=ignore,
            )

        if isinstance(question, appform.BooleanList):
            retval = [
                inquirer.Confirm(
                    question.variablename,
                    message=question.message,
                    default=question.default,
                    ignore=ignore,
                )
            ]

            if question.whenfalse:
                retval.extend(
                    [
                        self.assemble_questions(wf, ignore=question.ignore)
                        for wf in question.whenfalse
                    ]
                )
            if question.whentrue:
                retval.extend(
                    [
                        self.assemble_questions(wt, ignore=question.noignore)
                        for wt in question.whentrue
                    ]
                )

            return retval

        if isinstance(question, appform.Const):
            return inquirer.Text(
                question.variablename,
                message="",
                default=question.default,
                ignore=True,
            )

    def error_handle(self, error, solution):
        """
        Standardized error handling for CLI.

        Keyword Arguments:
            error     -- error generated
            solution  -- recommended  solution specific to each error
        """
        response = {"error": error, "solution": solution}
        return response

    def application_error_check(self, application_path):
        """
        Check for errors on application Create and Update.

        Confirms these are valid:
            dir provided by user for application path
            jobbergate.py in dir
            jobbergate.yaml in dir
        """
        error_check = []

        # check for required files
        local_jobbergate_application_dir = pathlib.Path(application_path)
        local_jobbergate_application_module = (
            local_jobbergate_application_dir / JOBBERGATE_APPLICATION_MODULE_FILE_NAME
        )
        local_jobbergate_application_config = (
            local_jobbergate_application_dir / JOBBERGATE_APPLICATION_CONFIG_FILE_NAME
        )

        if not local_jobbergate_application_dir.exists():
            check = self.error_handle(
                error="invalid application path supplied",
                solution=(
                    f"{application_path} is invalid, please " "review and try again"
                ),
            )
            error_check.append(check)
        if not local_jobbergate_application_module.exists():
            check = self.error_handle(
                error=(
                    f"Could not find {JOBBERGATE_APPLICATION_MODULE_FILE_NAME} "
                    "in {application_path}"
                ),
                solution=(
                    f"Please ensure {JOBBERGATE_APPLICATION_MODULE_FILE_NAME} "
                    "is in application path provided"
                ),
            )
            error_check.append(check)
        if not local_jobbergate_application_config.exists():
            check = self.error_handle(
                error=(
                    f"Could not find {JOBBERGATE_APPLICATION_CONFIG_FILE_NAME} "
                    "in {application_path}"
                ),
                solution=(
                    f"Please ensure {JOBBERGATE_APPLICATION_CONFIG_FILE_NAME} "
                    "is in application path provided"
                ),
            )
            error_check.append(check)

        return error_check

    @tabulate_decorator
    def list_job_scripts(self, all):
        """
        LIST Job Scripts.

        Keyword Arguments:
            all  -- optional parameter that will return all job scripts
                    if NOT specified then only the user's job scripts
                    will be returned
        """
        response = self.jobbergate_request(
            method="GET", endpoint=urljoin(self.api_endpoint, "/job-script/")
        )

        try:
            response = [
                {k: v for k, v in d.items() if k not in self.job_script_suppress}
                for d in response
            ]
        except:  # noqa: E722
            return response

        if all:
            return response
        else:
            response = [d for d in response if d["job_script_owner"] == self.user_id]
            return response

    @tabulate_decorator
    def create_job_script(
        self, job_script_name, application_id, param_file, sbatch_params, fast, debug
    ):
        """
        CREATE a Job Script.

        Keyword Arguments:
            name            --  Name for job script
            application-id  --  id of the application for the job script
            param-file      --  optional parameter file for populating templates.
                                if this is not provided, the question askin in
                                jobbergate.py is triggered
            sbatch-params   --  optional parameter to submit raw sbatch parameters
            fast            --  optional parameter to use default answers (when available)
                                instead of asking user
            debug           --  optional parameter to view job script data
                                in CLI output
        """
        if application_id is None:
            response = self.error_handle(
                error="--application-id for the job script not defined",
                solution="Please try again with --application-id specified",
            )
            return response

        if job_script_name is None:
            response = self.error_handle(
                error="--name for the job script not defined",
                solution="Please try again with --name specified",
            )
            return response

        self.validation_check = {}
        data = self.job_script_config
        data["job_script_name"] = job_script_name
        data["application"] = application_id
        data["job_script_owner"] = self.user_id

        if param_file:
            is_param_file = os.path.isfile(param_file)
            if is_param_file is False:
                response = self.error_handle(
                    error=f"invalid --parameter-file supplied: {param_file}",
                    solution="Provide the full path to a valid parameter file",
                )
                return response

            with open(param_file, "rb") as fh:
                supplied_params = json.loads(fh.read())
        else:
            supplied_params = {}

        app_data = self.jobbergate_request(
            method="GET", endpoint=urljoin(self.api_endpoint, f"/application/{application_id}")
        )
        if "error" in app_data.keys():
            return app_data

        # Get the jobbergate application python module
        JOBBERGATE_APPLICATION_MODULE_PATH.write_text(app_data["application_file"])
        # Get the jobbergate application yaml config
        JOBBERGATE_APPLICATION_CONFIG_PATH.write_text(app_data["application_config"])

        # Load the jobbergate yaml
        config = JOBBERGATE_APPLICATION_CONFIG_PATH.read_text()
        param_dict = yaml.load(config, Loader=yaml.FullLoader)

        # Exec the jobbergate application python module
        module = self.import_jobbergate_application_module()
        application = module.JobbergateApplication(param_dict)

        # Add all parameters from parameter file
        param_dict["jobbergate_config"].update(supplied_params)

        # Begin question assembly, starting in "mainflow" method
        param_dict["jobbergate_config"]["nextworkflow"] = "mainflow"

        while "nextworkflow" in param_dict["jobbergate_config"]:
            method_to_call = getattr(
                application, param_dict["jobbergate_config"].pop("nextworkflow")
            )  # Use and remove from the dict

            workflow_questions = method_to_call(data=param_dict["jobbergate_config"])

            questions = []
            auto_answers = {}

            while workflow_questions:
                field = workflow_questions.pop(0)
                # Use pre-defined answer or ask user
                if field.variablename in supplied_params.keys():
                    pass  # No further action needed, case kept here to visualize priority
                elif fast and field.default is not None:
                    print(f"Default value used: {field.variablename}={field.default}")
                    auto_answers[field.variablename] = field.default
                else:
                    # Prepare question for user
                    question = self.assemble_questions(field)
                    if isinstance(question, list):
                        questions.extend(question)
                    else:
                        questions.append(question)

            workflow_answers = inquirer.prompt(questions, raise_keyboard_interrupt=True)
            workflow_answers.update(auto_answers)
            param_dict["jobbergate_config"].update(workflow_answers)

        param_filename = f"{JOBBERGATE_CACHE_DIR}/param_dict.json"

        param_file = open(param_filename, "w")
        json.dump(param_dict, param_file)
        param_file.close()

        # TODO: Put below in function after testing - DRY
        files = {"upload_file": open(param_filename, "rb")}

        # Possibly overwrite script name
        if "job_script_name" in param_dict["jobbergate_config"]:
            data["job_script_name"] = param_dict["jobbergate_config"]["job_script_name"]

        if sbatch_params:
            for i, param in enumerate(sbatch_params):
                data["sbatch_params_" + str(i)] = param
            data["sbatch_params_len"] = len(sbatch_params)

        response = self.jobbergate_request(
            method="POST",
            endpoint=urljoin(self.api_endpoint, "/job-script/"),
            data=data,
            files=files,
        )
        if "error" in response.keys():
            return response

        try:
            rendered_dict = json.loads(response["job_script_data_as_string"])
        except:  # noqa: E722
            response = self.error_handle(
                error="could not load job_script_data_as_string from response",
                solution=f"Please review response: {response}",
            )
            return response

        job_script_data_as_string = ""
        for key, value in rendered_dict.items():
            job_script_data_as_string += "\n\nNEW_FILE\n\n"
            job_script_data_as_string += value

        response["job_script_data_as_string"] = job_script_data_as_string

        if debug is False:
            del response["job_script_data_as_string"]

        # Check if user wants to submit immediately
        if fast:
            submit = True
        else:
            submit = inquirer.prompt(
                [
                    inquirer.Confirm(
                        "sub",
                        message="Would you like to submit this immediately?",
                        default=True,
                    )
                ]
            )["sub"]

        # Write local copy of script and supporting files
        submission_result = self.create_job_submission(
            job_script_id=response["id"],
            render_only=not submit,
            job_submission_name=response["job_script_name"],
        )
        if submit:
            response["submission_result"] = submission_result

        return response

    @tabulate_decorator
    def get_job_script(self, job_script_id, as_str):
        """
        GET a Job Script.

        Keyword Arguments:
            job_script_id -- id of job script to be returned
            as_str        -- return job script as str in CLI output
        """
        if job_script_id is None:
            response = self.error_handle(
                error="--id not defined",
                solution="Please try again with --id specified",
            )
            return response

        response = self.jobbergate_request(
            method="GET", endpoint=urljoin(self.api_endpoint, f"/job-script/{job_script_id}")
        )
        if "error" in response.keys():
            return response

        rendered_dict = json.loads(response["job_script_data_as_string"])
        if as_str:
            return rendered_dict["application.sh"]
        else:
            job_script_data_as_string = ""
            for key, value in rendered_dict.items():
                job_script_data_as_string += "\nNEW_FILE\n"
                job_script_data_as_string += value

            response["job_script_data_as_string"] = job_script_data_as_string

            return response

    @tabulate_decorator
    def update_job_script(self, job_script_id, job_script_data_as_string):
        """
        UPDATE a Job Script.

        Keyword Arguments:
            job_script_id              -- id of job script to update
            job_script_data_as_string  -- data to update job script with
        """
        if job_script_id is None:
            response = self.error_handle(
                error="--id not defined",
                solution="Please try again with --id specified",
            )
            return response
        if job_script_data_as_string is None:
            response = self.error_handle(
                error="--job-script not defined",
                solution=f"Provide data to update ID: {job_script_id}",
            )
            return response

        data = self.jobbergate_request(
            method="GET", endpoint=urljoin(self.api_endpoint, f"/job-script/{job_script_id}")
        )
        if "error" in data.keys():
            return data
        data["job_script_data_as_string"] = job_script_data_as_string
        response = self.jobbergate_request(
            method="PUT",
            endpoint=urljoin(self.api_endpoint, f"/job-script/{job_script_id}/"),
            data=data,
        )

        return response

    @tabulate_decorator
    def delete_job_script(self, job_script_id):
        """
        DELETE a Job Script.

        Keyword Arguments:
            job_script_id -- id of job script to delete
        """
        if job_script_id is None:
            response = self.error_handle(
                error="--id not defined",
                solution="Please try again with --job-script-id specified",
            )
            return response

        response = self.jobbergate_request(
            method="DELETE", endpoint=urljoin(self.api_endpoint, f"/job-script/{job_script_id}")
        )

        return response

    # Job Submissions
    @tabulate_decorator
    def list_job_submissions(self, all):
        """
        LIST Job Submissions.

        Keyword Arguments:
            all  -- optional parameter that will return all job submissions
                    if NOT specified then only the user's job submissions
                    will be returned
        """
        response = self.jobbergate_request(
            method="GET", endpoint=urljoin(self.api_endpoint, "/job-submission/")
        )

        try:
            response = [
                {k: v for k, v in d.items() if k not in self.job_submission_suppress}
                for d in response
            ]
        except:  # noqa: E722
            return response

        if all:
            return response
        else:
            response = [
                d for d in response if d["job_submission_owner"] == self.user_id
            ]
            return response

    @tabulate_decorator
    def create_job_submission(self, job_script_id, render_only, job_submission_name=""):
        """
        CREATE Job Submission.

        Keyword Arguments:
            job_script_id -- id of job script to submit
            name          -- name for job submission
            render_only   -- create record in API and return data to CLI
                             but DO NOT submit job
        """
        if job_script_id is None:
            response = self.error_handle(
                error="--job-script-id not defined",
                solution="Please try again with --job-script-id specified",
            )
            return response

        data = self.job_submission_config
        data["job_submission_name"] = job_submission_name
        data["job_script"] = job_script_id
        data["job_submission_owner"] = self.user_id

        job_script = self.jobbergate_request(
            method="GET", endpoint=urljoin(self.api_endpoint, f"/job-script/{job_script_id}")
        )
        if "error" in job_script.keys():
            return job_script

        application_id = job_script["application"]

        application = self.jobbergate_request(
            method="GET", endpoint=urljoin(self.api_endpoint, f"/application/{application_id}")
        )
        if "error" in application.keys():
            return application

        application_name = application["application_name"]

        rendered_dict = json.loads(job_script["job_script_data_as_string"])

        script_filename = f'{job_script["job_script_name"]}.job'
        for key, value in rendered_dict.items():
            filename = key if key != "application.sh" else script_filename
            file_path = pathlib.Path.cwd() / filename
            file_path.write_text(value)
            # with open(filename, 'w') as write_file:
            #     write_file.write(value)

        if render_only:
            response = self.jobbergate_request(
                method="POST",
                endpoint=urljoin(self.api_endpoint, "/job-submission/"),
                data=data,
            )
            if "error" in response.keys():
                return response
        else:
            try:
                output, err, rc = self.jobbergate_run(script_filename, application_name)
            except FileNotFoundError:
                response = self.error_handle(
                    error="Failed to execute submission",
                    solution="Please confirm slurm sbatch is available",
                )
                return response

            if rc == 0:
                print(output)
                find = output.find("job") + 4
                slurm_job_id = output[find:]
                data["slurm_job_id"] = slurm_job_id
                response = self.jobbergate_request(
                    method="POST",
                    endpoint=urljoin(self.api_endpoint, "/job-submission/"),
                    data=data,
                )
                if "error" in response.keys():
                    return response
            else:
                response = self.error_handle(
                    error=f"Failed to execute submission with error: {err}",
                    solution="Please resolve error or contact for assistance",
                )
                return response
        return response

    @tabulate_decorator
    def get_job_submission(self, job_submission_id):
        """
        GET a Job Submission.

        Keyword Arguments:
            job_submission_id -- id of endpoint to action
        """
        if job_submission_id is None:
            response = self.error_handle(
                error="--id not defined",
                solution="Please try again with --id specified",
            )
            return response

        response = self.jobbergate_request(
            method="GET",
            endpoint=urljoin(self.api_endpoint, f"/job-submission/{job_submission_id}"),
        )

        return response

    @tabulate_decorator
    def update_job_submission(self, job_submission_id):
        """
        UPDATE a Job Submission.

        Keyword Arguments:
            job_submission_id -- id of job submission to update
        """
        if job_submission_id is None:
            response = self.error_handle(
                error="--id not defined",
                solution="Please try again with --id specified",
            )
            return response

        data = self.jobbergate_request(
            method="GET",
            endpoint=urljoin(self.api_endpoint, f"/job-submission/{job_submission_id}"),
        )
        if "error" in data.keys():
            return data
        # TODO how to collect data that will updated for the job-submission
        response = self.jobbergate_request(
            method="PUT",
            endpoint=urljoin(self.api_endpoint, f"/job-submission/{job_submission_id}/"),
        )
        return response

    @tabulate_decorator
    def delete_job_submission(self, job_submission_id):
        """
        Delete a Job Submission.

        Keyword Arguments:
            job_submission_id -- id of job submission to delete
        """
        if job_submission_id is None:
            response = self.error_handle(
                error="--id not defined",
                solution="Please try again with --id specified",
            )
            return response

        response = self.jobbergate_request(
            method="DELETE",
            endpoint=urljoin(self.api_endpoint, f"/job-submission/{job_submission_id}"),
        )

        return response

    # Applications
    @tabulate_decorator
    def list_applications(self, all):
        """
        LIST available applications.

        Keyword Arguments:
            all  -- optional parameter that will return all applications
                    if NOT specified then only the user's applications
                    will be returned
        """
        response = self.jobbergate_request(
            method="GET", endpoint=urljoin(self.api_endpoint, "/application/")
        )
        try:
            response = [
                {k: v for k, v in d.items() if k not in self.application_suppress}
                for d in response
            ]
        except:  # noqa: E722
            return response

        # Sort
        response.sort(key=lambda app: app["id"], reverse=True)

        if all:
            return response
        else:
            response = [d for d in response if d["application_owner"] == self.user_id]
            return response

    @tabulate_decorator
    def create_application(self, application_name, application_path, application_desc):
        """
        CREATE an application.

        Keyword Arguments:
            application_name -- Name of the application
            application_path -- path to dir where application files are
        """
        parameter_check = []
        if application_name is None:
            response = self.error_handle(
                error="--name not defined",
                solution="Please try again with --name specified",
            )
            parameter_check.append(response)

        if application_path is None:
            response = self.error_handle(
                error="--application-path not defined",
                solution="Please try again with --application-path specified",
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
        data["application_name"] = application_name
        data["application_owner"] = self.user_id

        if application_desc:
            data["application_description"] = application_desc

        tar_list = [application_path, os.path.join(application_path, "templates")]
        self.tardir(application_path, TAR_NAME, tar_list)

        files = {"upload_file": open(TAR_NAME, "rb")}

        response = self.jobbergate_request(
            method="POST",
            endpoint=urljoin(self.api_endpoint, "/application/"),
            data=data,
            files=files,
        )
        if "error" in response.keys():
            return response

        try:
            for key in self.application_suppress:
                response.pop(key, None)
        except AttributeError:
            # response is str of error message
            return response

        os.remove(TAR_NAME)

        return response

    @tabulate_decorator
    def get_application(self, application_id):
        """
        GET an Application.

        Keyword Arguments:
            application_id -- id of application to be returned
        """
        response = self.jobbergate_request(
            method="GET", endpoint=urljoin(self.api_endpoint, f"/application/{application_id}")
        )

        return response

    @tabulate_decorator
    def update_application(self, application_id, application_path, application_desc):
        """
        UPDATE an Application.

        Keyword Arguments:
            application_id    -- id application to update
            application_path  --  path to dir for updated application files
            application_desc  --  optional new application description
        """
        if application_path is None:
            response = self.error_handle(
                error="--application-path not defined",
                solution="Please try again with --application-path specified",
            )
            return response

        error_check = self.application_error_check(application_path)

        if len(error_check) > 0:
            response = error_check
            return response

        data = self.jobbergate_request(
            method="GET", endpoint=urljoin(self.api_endpoint, f"/application/{application_id}")
        )
        if "error" in data.keys():
            return data

        del data["id"]
        del data["created_at"]
        del data["updated_at"]
        if application_desc:
            data["application_description"] = application_desc

        tar_list = [application_path, os.path.join(application_path, "templates")]
        self.tardir(application_path, TAR_NAME, tar_list)

        files = {"upload_file": open(TAR_NAME, "rb")}

        response = self.jobbergate_request(
            method="PUT",
            endpoint=urljoin(self.api_endpoint, f"/application/{application_id}/"),
            data=data,
            files=files,
        )
        if "error" in response.keys():
            return response

        try:
            for key in self.application_suppress:
                response.pop(key, None)

            os.remove(TAR_NAME)
        except AttributeError:
            # response is str of error message
            return response
        return response

    @tabulate_decorator
    def delete_application(self, application_id):
        """
        DELETE an Application.

        Keyword Arguments:
            application_id -- id of application to delete
        """
        response = self.jobbergate_request(
            method="DELETE",
            endpoint=urljoin(self.api_endpoint, f"/application/{application_id}"),
        )

        return response
