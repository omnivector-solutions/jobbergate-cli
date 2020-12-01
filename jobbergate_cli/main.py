#!/usr/bin/env python3
from datetime import datetime
import getpass
from pathlib import Path
import sys

import click
import jwt
import requests

from jobbergate_cli import client
from jobbergate_cli.jobbergate_api_wrapper import JobbergateApi
from jobbergate_cli.jobbergate_common import (
    JOBBERGATE_API_ENDPOINT,
    JOBBERGATE_API_JWT_PATH,
    JOBBERGATE_API_OBTAIN_TOKEN_ENDPOINT,
    JOBBERGATE_APPLICATION_CONFIG,
    JOBBERGATE_DEBUG,
    JOBBERGATE_JOB_SCRIPT_CONFIG,
    JOBBERGATE_JOB_SUBMISSION_CONFIG,
    JOBBERGATE_USER_TOKEN_DIR,
)


class Api(object):
    def __init__(self, user_id=None):
        self.api = JobbergateApi(
            token=JOBBERGATE_API_JWT_PATH.read_text(),
            job_script_config=JOBBERGATE_JOB_SCRIPT_CONFIG,
            job_submission_config=JOBBERGATE_JOB_SUBMISSION_CONFIG,
            application_config=JOBBERGATE_APPLICATION_CONFIG,
            api_endpoint=JOBBERGATE_API_ENDPOINT,
            user_id=user_id,
        )


def interactive_get_username_password():
    username = input("Please enter your username: ")
    password = getpass.getpass()
    return username, password


def init_token(username, password):
    """Get a new token from the api and write it to the token file."""
    resp = client.post(
        JOBBERGATE_API_OBTAIN_TOKEN_ENDPOINT,
        data={"email": username, "password": password},
    )
    data = resp.json()
    ret = data.get("token")
    JOBBERGATE_API_JWT_PATH.write_text(ret)


def is_token_valid():
    """
    Return true/false depending on whether the token is valid or not.
    """
    token = dict()

    if JOBBERGATE_API_JWT_PATH.exists():
        token = decode_token_to_dict(JOBBERGATE_API_JWT_PATH.read_text())
        if datetime.fromtimestamp(token["exp"]) > datetime.now():
            return True
        else:
            return False
    else:
        return False


def decode_token_to_dict(encoded_token):
    """
    Decode Auth token to dict
    """
    try:
        token = jwt.decode(
            encoded_token,
            verify=False,
        )
    except jwt.exceptions.InvalidTokenError as e:
        print(e)
        # FIXME - raise an exception (and catch, then ctx.exit())
        sys.exit()
    return token


def init_api(user_id):
    """Initialize the API for the user's session."""
    api = JobbergateApi(
        token=JOBBERGATE_API_JWT_PATH.read_text(),
        job_script_config=JOBBERGATE_JOB_SCRIPT_CONFIG,
        job_submission_config=JOBBERGATE_JOB_SUBMISSION_CONFIG,
        application_config=JOBBERGATE_APPLICATION_CONFIG,
        api_endpoint=JOBBERGATE_API_ENDPOINT,
        user_id=user_id,
    )
    return api


# Get the cli input arguments
# args = get_parsed_args(argv)
# Grab the pre-existing token, if doesn't exist
# or is invalid then grab a new one.
#
# Allow the user to pass their jobbergate username and password as command line
# arguments. If a token isn't found or invalid AND the username and password
# are not supplied at runtime, we will launch an interactive session to
# acquire the username password.


# def get_parsed_args(argv):
"""Create argument parser and return cli args.
"""


# Get the cli input arguments
@click.group()
@click.option(
    "--username",
    "-u",
    help="Your Jobbergate API Username",
)
@click.option("--password", "-p", help="Your Jobbergate API password", hide_input=True)
@click.version_option()
@click.pass_context
def main(ctx, username, password):
    """
    Controls flow.

    ctx --> context
    @click.pass_context makes username, password,
    token and user_id available to the other cmd
    """
    ctx.ensure_object(dict)

    # create dir for token if it doesnt exist
    Path(JOBBERGATE_USER_TOKEN_DIR).mkdir(parents=True, exist_ok=True)

    if JOBBERGATE_DEBUG:
        client.debug_requests_on()

    if not is_token_valid():
        if username and password:
            ctx.obj["username"] = username
            ctx.obj["password"] = password
        else:
            username, password = interactive_get_username_password()
            ctx.obj["username"] = username
            ctx.obj["password"] = password
        try:
            init_token(username, password)
        except KeyError:
            print(f"Auth Failed for username: {username}, please try again")
            sys.exit(0)  # FIXME - ctx.exit() instead
        except TypeError:
            print("Password cannot be empty, please try again")
            sys.exit(0)  # FIXME - ctx.exit() instead
        except requests.exceptions.ConnectionError:
            print("Auth failed to establish connection with API, please try again")
            sys.exit(0)  # FIXME - ctx.exit() instead

    ctx.obj["token"] = decode_token_to_dict(JOBBERGATE_API_JWT_PATH.read_text())

    ctx.obj = Api(user_id=ctx.obj["token"]["user_id"])


@main.command("list-applications")
@click.option("--all", "all", is_flag=True)
@click.pass_obj
def list_applications(ctx, all=False):
    """
    LIST available applications.

    Keyword Arguments:
        all  -- optional parameter that will return all applications
                if NOT specified then only the user's applications
                will be returned
    """
    print(ctx.api.list_applications(all))


@main.command("create-application")
@click.option("--name", "-n", "create_application_name")
@click.option("--application-path", "-a", "create_application_path")
@click.option("--application-desc", "application_desc", default="")
@click.pass_obj
def create_application(
    ctx, create_application_name, create_application_path, application_desc
):
    """
    CREATE an application.

    Keyword Arguments:
        name             -- Name of the application
        application-path -- path to dir where application files are
    """
    out = ctx.api.create_application(
        application_name=create_application_name,
        application_path=create_application_path,
        application_desc=application_desc,
    )
    print(out)


@main.command("get-application")
@click.option("--id", "-i", "application_id")
@click.pass_obj
def get_application(ctx, application_id):
    """
    GET an Application.

    Keyword Arguments:
        id -- id of application to be returned
    """
    print(ctx.api.get_application(application_id=application_id))


@main.command("update-application")
@click.option("--id", "-i", "update_application_id")
@click.option("--application-path", "-a", "application_path")
@click.option("--application-desc", "application_desc", default="")
@click.pass_obj
def update_application(ctx, update_application_id, application_path, application_desc):
    """
    UPDATE an Application.

    Keyword Arguments:
        id                --  id application to update
        application-path  --  path to dir for updated application files
        application-desc  --  optional new application description
    """
    print(
        ctx.api.update_application(
            update_application_id, application_path, application_desc
        )
    )


@main.command("delete-application")
@click.option("--id", "-i", "delete_application_id")
@click.pass_obj
def delete_application(ctx, delete_application_id):
    """
    DELETE an Application.

    Keyword Arguments:
        id -- id of application to delete
    """
    print(ctx.api.delete_application(delete_application_id))


@main.command("list-job-scripts")
@click.option("--all", "all", is_flag=True)
@click.pass_obj
def list_job_scripts(ctx, all=False):
    """
    LIST Job Scripts.

    Keyword Arguments:
        all  -- optional parameter that will return all job scripts
                if NOT specified then only the user's job scripts
                will be returned
    """
    print(ctx.api.list_job_scripts(all))


@main.command("create-job-script")
@click.option("--name", "-n", "create_job_script_name", default="default_script_name")
@click.option("--application-id", "-i", "create_job_script_application_id")
@click.option(
    "--param-file",
    "param_file",
    type=click.Path(),
)
@click.option("--fast", "-f", "fast", is_flag=True)
@click.option("--debug", "debug", is_flag=True)
@click.pass_obj
def create_job_script(
    ctx,
    create_job_script_name,
    create_job_script_application_id,
    param_file=None,
    fast=False,
    debug=False,
):
    """
    CREATE a Job Script.

    Keyword Arguments:
        name            --  Name for job script
        application-id  --  id of the application for the job script
        param-file      --  optional parameter file for populating templates.
                            if answers are not provided, the question asking in
                            jobbergate.py is triggered
        fast            --  optional parameter to use default answers (when available)
                            instead of asking user
        debug           --  optional parameter to view job script data in CLI output
    """
    print(
        ctx.api.create_job_script(
            create_job_script_name,
            create_job_script_application_id,
            param_file,
            fast,
            debug,
        )
    )


@main.command("get-job-script")
@click.option("--id", "-i", "get_job_script_id")
@click.option("--as-string", "as_str", is_flag=True)
@click.pass_obj
def get_job_script(ctx, get_job_script_id, as_str):
    """
    GET a Job Script.

    Keyword Arguments:
        id -- id of job script to be returned
    """
    print(ctx.api.get_job_script(get_job_script_id, as_str))


@main.command("update-job-script")
@click.option("--id", "-i", "update_job_script_id")
@click.option("--job-script", "job_script_data_as_string")
@click.pass_obj
def update_job_script(ctx, update_job_script_id, job_script_data_as_string):
    """
    UPDATE a Job Script.

    Keyword Arguments: \n
        id          -- id of job script to update \n
        job-script  -- data with which to update job script \n
                       format: string form of dictionary with main script as entry "application.sh" \n
                       e.g. '{"application.sh":"#!/bin/bash \\n hostname"}'
    """
    print(ctx.api.update_job_script(update_job_script_id, job_script_data_as_string))


@main.command("delete-job-script")
@click.option("--id", "-i", "delete_job_script_id")
@click.pass_obj
def delete_job_script(ctx, delete_job_script_id):
    """
    DELETE a Job Script.

    Keyword Arguments:
        id -- id of job script to delete
    """
    print(ctx.api.delete_job_script(delete_job_script_id))


@main.command("list-job-submissions")
@click.option("--all", "all", is_flag=True)
@click.pass_obj
def list_job_submissions(ctx, all=False):
    """
    LIST Job Submissions.

    Keyword Arguments:
        all  -- optional parameter that will return all job submissions
                if NOT specified then only the user's job submissions
                will be returned
    """
    print(ctx.api.list_job_submissions(all))


@main.command("create-job-submission")
@click.option("--job-script-id", "-i", "create_job_submission_job_script_id")
@click.option("--name", "create_job_submission_name")
@click.option("--dry-run", "render_only")
@click.pass_obj
def create_job_submission(
    ctx,
    create_job_submission_job_script_id,
    create_job_submission_name="",
    render_only=None,
):
    """
    CREATE Job Submission.

    Keyword Arguments:
        job-script-id -- id of job script to submit
        name          -- name for job submission
        dry-run       -- create record in API and return data to CLI
                         but DO NOT submit job
    """
    print(
        ctx.api.create_job_submission(
            job_script_id=create_job_submission_job_script_id,
            job_submission_name=create_job_submission_name,
            render_only=render_only,
        )
    )


@main.command("get-job-submission")
@click.option("--id", "-i", "get_job_submission_id")
@click.pass_obj
def get_job_submission(ctx, get_job_submission_id):
    """
    GET a Job Submission.

    Keyword Arguments:
        id -- id of endpoint to action
    """
    print(ctx.api.get_job_submission(get_job_submission_id))


@main.command("update-job-submission")
@click.option("--id", "-i", "update_job_submission_id")
@click.pass_obj
def update_job_submission(ctx, update_job_submission_id):
    """
    UPDATE a Job Submission.

    Keyword Arguments:
        id -- id of job submission to update
    """
    print(ctx.api.update_job_submission(update_job_submission_id))


@main.command("delete-job-submission")
@click.option("--id", "-i", "delete_job_submission_id")
@click.pass_obj
def delete_job_submission(ctx, delete_job_submission_id):
    """
    Delete a Job Submission.

    Keyword Arguments:
        id -- id of job submission to delete
    """
    print(ctx.api.delete_job_submission(delete_job_submission_id))


if __name__ == "__main__":
    main()
