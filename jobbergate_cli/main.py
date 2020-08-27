#!/usr/bin/env python3
import getpass
import requests
import sys
from pathlib import Path

import jwt

import click
from datetime import datetime

from jobbergate_cli.jobbergate_api_wrapper import JobbergateApi
from jobbergate_cli.jobbergate_common import (
    JOB_SCRIPT_CONFIG,
    JOB_SUBMISSION_CONFIG,
    JOBBERGATE_API_JWT_PATH,
    JOBBERGATE_API_ENDPOINT,
    JOBBERGATE_API_OBTAIN_TOKEN_ENDPOINT,
    JOBBERGATE_APPLICATION_BASE_PATH,
    JOBBERGATE_APPLICATION_CONFIG,
    JOBBERGATE_USER_TOKEN_DIR,
)


class Api(object):
    def __init__(self, user_id=None):
        self.api = JobbergateApi(
            token=JOBBERGATE_API_JWT_PATH.read_text(),
            job_script_config=JOB_SCRIPT_CONFIG,
            job_submission_config=JOB_SUBMISSION_CONFIG,
            application_config=JOBBERGATE_APPLICATION_CONFIG,
            api_endpoint=JOBBERGATE_API_ENDPOINT,
            user_id=user_id)


def interactive_get_username_password():
    username = input("Please enter your username: ")
    password = getpass.getpass()
    return username, password


def init_token(username, password):
    """Get a new token from the api and write it to the token file.
    """
    resp = requests.post(
        JOBBERGATE_API_OBTAIN_TOKEN_ENDPOINT,
        data={"email": username, "password": password}
    )
    # if resp.status_code == 502:
    #
    JOBBERGATE_API_JWT_PATH.write_text(resp.json()['token'])



def is_token_valid():
    """Return true/false depending on whether the token is valid or not.
    """
    token = dict()

    if JOBBERGATE_API_JWT_PATH.exists():
        token = decode_token_to_dict(JOBBERGATE_API_JWT_PATH.read_text())
        if datetime.fromtimestamp(token['exp']) > datetime.now():
            return True
        else:
            return False
    else:
        return False


def decode_token_to_dict(encoded_token):
    try:
        token = jwt.decode(
            encoded_token,
            verify=False,
        )
    except jwt.exceptions.InvalidTokenError as e:
        print(e)
        sys.exit()
    return token


def init_api(user_id):
    api = JobbergateApi(
        token=JOBBERGATE_API_JWT_PATH.read_text(),
        job_script_config=JOB_SCRIPT_CONFIG,
        job_submission_config=JOB_SUBMISSION_CONFIG,
        application_config=JOBBERGATE_APPLICATION_CONFIG,
        api_endpoint=JOBBERGATE_API_ENDPOINT,
        user_id=user_id)
    return api


def load_config():
    pass

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
    '--username',
    '-u',
    help='Your Jobbergate API Username',
)
@click.option(
    '--password', '-p',
    help='Your Jobbergate API password',
    hide_input=True
)
@click.pass_context
def main(ctx,
         username,
         password):
    """
    ctx --> context
    @click.pass_context makes username, password,
    token and user_id available to the other cmd
    """
    ctx.ensure_object(dict)

    # create dir for token if it doesnt exist
    Path(JOBBERGATE_USER_TOKEN_DIR).mkdir(parents=True, exist_ok=True)

    if not is_token_valid():
        if username and password:
            ctx.obj['username'] = username
            ctx.obj['password'] = password
        else:
            username, password = interactive_get_username_password()
            ctx.obj['username'] = username
            ctx.obj['password'] = password
        try:
            init_token(username, password)
        except KeyError:
            print(
                f"Auth Failed for username: {username}, Please Try again"
            )
            sys.exit(0)
    ctx.obj['token'] = decode_token_to_dict(
        JOBBERGATE_API_JWT_PATH.read_text())

    ctx.obj = Api(user_id=ctx.obj['token']['user_id'])


@main.command('list-applications')
@click.option("--all",
              "all",
              is_flag=True)
@click.pass_obj
def list_applications(ctx, all=False):
    print(ctx.api.list_applications(all))


@main.command('create-application')
@click.option("--name",
              "-n",
              "create_application_name")
@click.option("--application-path",
              "-a",
              "create_application_path")
@click.option("--application-desc",
              "application_desc",
              default="")
@click.pass_obj
def create_application(ctx,
                       create_application_name,
                       create_application_path,
                       application_desc):
    """Creates a jobbergate application."""
    out = ctx.api.create_application(
            application_name=create_application_name,
            application_path=create_application_path,
            application_desc=application_desc,
    )
    print(out)


@main.command('get-application')
@click.option("--id",
              "-i",
              "application_id")
@click.pass_obj
def get_application(ctx,
                    application_id):
    print(ctx.api.get_application(
        application_id=application_id))


@main.command('update-application')
@click.option("--id",
              "-i",
              "update_application_id")
@click.pass_obj
def update_application(ctx,
                       update_application_id):
    print(ctx.api.update_application(update_application_id))


@main.command('delete-application')
@click.option("--id",
              "-i",
              "delete_application_id")
@click.pass_obj
def delete_application(ctx,
                       delete_application_id):
    print(ctx.api.delete_application(delete_application_id))


@main.command('list-job-scripts')
@click.option("--all",
              "all",
              is_flag=True)
@click.pass_obj
def list_job_scripts(ctx, all=False):
    print(ctx.api.list_job_scripts(all))


@main.command('create-job-script')
@click.option("--name",
              "-n",
              "create_job_script_name")
@click.option("--application-id",
              "-i",
              "create_job_script_application_id")
@click.option("--param-file",
              "-p",
              "param_file",
              type=click.Path(),)
@click.option("--debug",
              "debug",
              is_flag=True)
@click.pass_obj
def create_job_script(ctx,
                      create_job_script_name,
                      create_job_script_application_id,
                      debug=False,
                      param_file=None):
    print(ctx.api.create_job_script(
        create_job_script_name,
        create_job_script_application_id,
        param_file,
        debug))


@main.command('get-job-script')
@click.option("--id",
              "-i",
              "get_job_script_id")
@click.option("--as-string",
              "as_str",
              is_flag=True)
@click.pass_obj
def get_job_script(ctx,
                   get_job_script_id,
                   as_str):
    print(ctx.api.get_job_script(get_job_script_id, as_str))


@main.command('update-job-script')
@click.option("--id",
              "-i",
              "update_job_script_id")
@click.pass_obj
def update_job_script(ctx,
                      update_job_script_id):
    print(ctx.api.update_job_script(update_job_script_id))


@main.command('delete-job-script')
@click.option("--id",
              "-i",
              "delete_job_script_id")
@click.pass_obj
def delete_job_script(ctx,
                      delete_job_script_id):
    print(ctx.api.delete_job_script(delete_job_script_id))


@main.command('list-job-submissions')
@click.option("--all",
              "all",
              is_flag=True)
@click.pass_obj
def list_job_submissions(ctx, all=False):
    print(ctx.api.list_job_submissions(all))


@main.command('create-job-submission')
@click.option("--name",
              "-n",
              "create_job_submission_name")
@click.option("--job-script-id",
              "-i",
              "create_job_submission_job_script_id")
@click.option("--dry-run",
              "render_only")
@click.pass_obj
def create_job_submission(ctx,
                          create_job_submission_name,
                          create_job_submission_job_script_id,
                          render_only=None):
    print(ctx.api.create_job_submission(
        create_job_submission_name,
        create_job_submission_job_script_id,
        render_only))


@main.command('get-job-submission')
@click.option("--id",
              "-i",
              "get_job_submission_id")
@click.pass_obj
def get_job_submission(ctx,
                       get_job_submission_id):
    print(ctx.api.get_job_submission(get_job_submission_id))


@main.command('update-job-submission')
@click.option("--id",
              "-i",
              "update_job_submission_id")
@click.pass_obj
def update_job_submission(ctx,
                          update_job_submission_id):
    print(ctx.api.update_job_submission(update_job_submission_id))


@main.command('delete-job-submission')
@click.option("--id",
              "-i",
              "delete_job_submission_id")
@click.pass_obj
def delete_job_submission(ctx,
                          delete_job_submission_id):
    print(ctx.api.delete_job_submission(delete_job_submission_id))


if __name__ == "__main__":
    main()
