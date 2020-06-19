#!/usr/bin/env python3
import getpass
import json
import requests
from requests_jwt import JWTAuth
import sys
import os

import jwt

import click
from datetime import datetime
from pathlib import Path

from jobbergate_cli.jobbergate_api_wrapper import JobbergateApi


JOBBERGATE_API_JWT_PATH = Path("/tmp/jobbergate.token")

JOBBERGATE_API_ENDPOINT = "http://0.0.0.0:8000"

JOBBERGATE_API_OBTAIN_TOKEN_ENDPOINT = f"{JOBBERGATE_API_ENDPOINT}/api-token-auth/"

dir_path = os.path.dirname(os.path.realpath(__file__))

JOB_SCRIPT_CONFIG = os.path.join(dir_path, "config", "jobscript.json")

JOB_SUBMISSION_CONFIG = os.path.join(dir_path, "config", "jobsubmission.json")

APPLICATION_CONFIG = os.path.join(dir_path, "config", "application.json")


def interactive_get_username_password():
    username = input("Please enter your username: ")
    password = getpass.getpass()
    return username, password


def init_token(username, password):
    """Get a new token from the api and write it to the token file.
    """
    resp = requests.post(
        JOBBERGATE_API_OBTAIN_TOKEN_ENDPOINT,
        data={"username": username, "password": password}
    )
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
        application_config=APPLICATION_CONFIG,
        api_endpoint=JOBBERGATE_API_ENDPOINT,
        user_id=user_id)
    return api


# Get the cli input arguments
# args = get_parsed_args(argv)
# Grab the pre-existing token, if doesn't exist or is invalid then grab a new one.
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
def main(ctx, username, password):
    print("hit main function")
    """
    ctx --> context
    @click.pass_context makes username, password, token and user_id available to the other cmd
    """
    ctx.ensure_object(dict)
    if not is_token_valid():
        if username and password:
            ctx.obj['username'] = username
            ctx.obj['password'] = password
        else:
            username, password = interactive_get_username_password()
            ctx.obj['username'] = username
            ctx.obj['password'] = password
        init_token(username, password)
    ctx.obj['token'] = decode_token_to_dict(JOBBERGATE_API_JWT_PATH.read_text())
    ctx.obj['user_id'] = ctx.obj['token']['user_id']

@main.command('list-applications')
@click.pass_context
def list_applications(ctx):
    print(f"testing list-app")
    api = init_api(ctx.obj['user_id'])
    resp = api.list_applications()
    sys.stdout.write(str(resp))
    sys.exit(0)

@main.command('create-application')
@click.option("--name",
              "-n",
              "create_application_name")
@click.pass_context
def create_application(ctx, create_application_name):
    api = init_api(ctx.obj['user_id'])
    resp = api.create_application(create_application_name)
    sys.stdout.write(str(resp))
    sys.exit(0)


@main.command('get-application')
@click.option("--id",
              "-i",
              "get_application_id")
@click.pass_context
def get_application(ctx, get_application_id):
    api = init_api(ctx.obj['user_id'])
    resp = api.get_application(get_application_id)
    sys.stdout.write(str(resp))
    sys.exit(0)

@main.command('update-application')
@click.option("--id",
              "-i",
              "update_application_id")
@click.pass_context
def update_application(ctx, update_application_id):
    api = init_api(ctx.obj['user_id'])
    resp = api.update_application(update_application_id)
    sys.stdout.write(str(resp))
    sys.exit(0)

@main.command('delete-application')
@click.option("--id",
              "-i",
              "delete_application_id")
@click.pass_context
def delete_application(ctx, delete_application_id):
    api = init_api(ctx.obj['user_id'])
    resp = api.delete_application(delete_application_id)
    sys.stdout.write(str(resp))
    sys.exit(0)

@main.command('list-job-scripts')
@click.pass_context
def list_job_scripts(ctx):
    api = init_api(ctx.obj['user_id'])
    resp = api.list_job_scripts()
    sys.stdout.write(str(resp))
    sys.exit(0)

@main.command('create-job-script')
@click.option("--name",
              "-n",
              "create_job_script_name")
@click.option("--id",
              "-i",
              "create_job_script_application_id")
@click.pass_context
def create_job_script(ctx, create_job_script_name, create_job_script_application_id):
    api = init_api(ctx.obj['user_id'])
    resp = api.create_job_script(create_job_script_name, create_job_script_application_id)
    sys.stdout.write(str(resp))
    sys.exit(0)


@main.command('get-job-script')
@click.option("--id",
              "-i",
              "get_job_script_id")
@click.pass_context
def get_job_script(ctx, get_job_script_id):
    api = init_api(ctx.obj['user_id'])
    resp = api.get_job_script(get_job_script_id)
    sys.stdout.write(str(resp))
    sys.exit(0)

@main.command('update-job-script')
@click.option("--id",
              "-i",
              "update_job_script_id")
@click.pass_context
def update_job_script(ctx, update_job_script_id):
    api = init_api(ctx.obj['user_id'])
    resp = api.update_job_script(update_job_script_id)
    sys.stdout.write(str(resp))
    sys.exit(0)

@main.command('delete-job-script')
@click.option("--id",
              "-i",
              "delete_job_script_id")
@click.pass_context
def delete_job_script(ctx, delete_job_script_id):
    api = init_api(ctx.obj['user_id'])
    resp = api.delete_job_script(delete_job_script_id)
    sys.stdout.write(str(resp))
    sys.exit(0)

@main.command('list-job-submissions')
@click.pass_context
def list_job_submissions(ctx):
    api = init_api(ctx.obj['user_id'])
    resp = api.list_job_submissions()
    sys.stdout.write(str(resp))
    sys.exit(0)

@main.command('create-job-submission')
@click.option("--name",
              "-n",
              "create_job_submission_name")
@click.option("--id",
              "-i",
              "create_job_submission_job_script_id")
@click.pass_context
def create_job_submission(ctx, create_job_submission_name, create_job_submission_job_script_id):
    api = init_api(ctx.obj['user_id'])
    resp = api.create_job_submission(create_job_submission_name, create_job_submission_job_script_id)
    sys.stdout.write(str(resp))
    sys.exit(0)


@main.command('get-job-submission')
@click.option("--id",
              "-i",
              "get_job_submission_id")
@click.pass_context
def get_job_submission(ctx, get_job_submission_id):
    api = init_api(ctx.obj['user_id'])
    resp = api.get_job_submission(get_job_submission_id)
    sys.stdout.write(str(resp))
    sys.exit(0)

@main.command('update-job-submission')
@click.option("--id",
              "-i",
              "update_job_submission_id")
@click.pass_context
def update_job_submission(ctx, update_job_submission_id):
    api = init_api(ctx.obj['user_id'])
    resp = api.update_job_submission(update_job_submission_id)
    sys.stdout.write(str(resp))
    sys.exit(0)

@main.command('delete-job-submission')
@click.option("--id",
              "-i",
              "delete_job_submission_id")
@click.pass_context
def delete_job_submission(ctx, delete_job_submission_id):
    api = init_api(ctx.obj['user_id'])
    resp = api.delete_job_submission(delete_job_submission_id)
    sys.stdout.write(str(resp))
    sys.exit(0)


if __name__ == "__main__":
    main()


# parser.add_argument(
#     '-u',
#     '--username',
#     dest='username',
#     required=False,
#     help="Jobbergate username",
# )
#
# parser.add_argument(
#     '-p',
#     '--password',
#     dest='password',
#     required=False,
#     help="Jobbergate password",
# )
#
# subparsers = parser.add_subparsers(
#     title="commands",
#     dest="command",
#     help="Jobbergate CLI Operations.",
# )
#
# # Applications
# list_applications_parser = subparsers.add_parser(
# # parser.add_argument(
#     "list-applications",
#     help="List applications.",
# )
#
# create_application_parser = subparsers.add_parser(
#     "create-application",
#     help="Create an application.",
# )
# create_application_parser.add_argument(
#     "-n",
#     "--name",
#     required=True,
#     dest="create_application_name",
#     help="Name of the application.",
# )
#
# get_application_parser = subparsers.add_parser(
#     "get-application",
#     help="Return an application.",
# )
# get_application_parser.add_argument(
#     "-i",
#     "--id",
#     required=True,
#     dest="get_application_id",
#     help="Application id.",
# )
#
# update_application_parser = subparsers.add_parser(
#     "update-application",
#     help="Update an application.",
# )
# update_application_parser.add_argument(
#     "-i",
#     "--id",
#     required=True,
#     dest="update_application_id",
#     help="Id of the desired application to update.",
# )
#
# delete_application_parser = subparsers.add_parser(
#     "delete-application",
#     help="Delete an application.",
# )
# delete_application_parser.add_argument(
#     "-i",
#     "--id",
#     required=True,
#     dest="delete_application_id",
#     help="Id of the desired application to delete.",
# )
#
# # Job Scripts
# list_job_scripts_parser = subparsers.add_parser(
#     "list-job-scripts",
#     help="List job scripts.",
# )
#
# create_job_script_parser = subparsers.add_parser(
#     "create-job-script",
#     help="Create a job-script",
# )
# create_job_script_parser.add_argument(
#     "-n",
#     "--name",
#     required=True,
#     dest="create_job_script_name",
#     help="Name of the job-script to create.",
# )
#
# create_job_script_parser.add_argument(
#     "-i",
#     "--id",
#     required=True,
#     dest="create_job_script_application_id",
#     help="id of the application for job-script to create.",
# )
#
# get_job_script_parser = subparsers.add_parser(
#     "get-job-script",
#     help="Return a job-script",
# )
# get_job_script_parser.add_argument(
#     "-i",
#     "--id",
#     required=True,
#     dest="get_job_script_id",
#     help="Id of the desired job script to return.",
# )
#
# update_job_script_parser = subparsers.add_parser(
#     "update-job-script",
#     help="Update a job-script",
# )
# update_job_script_parser.add_argument(
#     "-i",
#     "--id",
#     required=True,
#     dest="update_job_script_id",
#     help="Id of the desired job script to update.",
# )
#
# delete_job_script_parser = subparsers.add_parser(
#     "delete-job-script",
#     help="Delete a job-script",
# )
# delete_job_script_parser.add_argument(
#     "-i",
#     "--id",
#     required=True,
#     dest="delete_job_script_id",
#     help="Id of the desired job script to delete.",
# )
#
# # Job Submissions
# list_job_submissions_parser = subparsers.add_parser(
#     "list-job-submissions",
#     help="List job submissions.",
# )
#
# create_job_submission_parser = subparsers.add_parser(
#     "create-job-submission",
#     help="Create a job submission.",
# )
# create_job_submission_parser.add_argument(
#     "-n",
#     "--name",
#     required=True,
#     dest="create_job_submission_name",
#     help="Name of the job submission.",
# )
#
# create_job_submission_parser.add_argument(
#     "-i",
#     "--id",
#     required=True,
#     dest="create_job_submission_job_script_id",
#     help="id of the job script for the job submission.",
# )
#
# get_job_submission_parser = subparsers.add_parser(
#     "get-job-submission",
#     help="Return a job submission",
# )
# get_job_submission_parser.add_argument(
#     "-i",
#     "--id",
#     required=True,
#     dest="get_job_submission_id",
#     help="Id of the desired job submission to return.",
# )
#
# update_job_submission_parser = subparsers.add_parser(
#     "update-job-submission",
#     help="Update a job submission.",
# )
# update_job_submission_parser.add_argument(
#     "-i",
#     "--id",
#     required=True,
#     dest="update_job_submission_id",
#     help="Id of the desired job submission to update.",
# )
#
# delete_job_submission_parser = subparsers.add_parser(
#     "delete-job-submission",
#     help="Delete a job submission.",
# )
# delete_job_submission_parser.add_argument(
#     "-i",
#     "--id",
#     required=True,
#     dest="delete_job_submission_id",
#     help="Id of the desired job submission to delete.",
# )
#
# args = parser.parse_args()
#
#
# # Job Scripts
# if args.command == 'list-job-scripts':
#     resp = api.list_job_scripts()
#     sys.stdout.write(str(resp))
#     sys.exit(0)
#
# if args.command == 'create-job-script':
#     resp = api.create_job_script(
#         args.create_job_script_name,
#         args.create_job_script_application_id,
#     )
#     sys.stdout.write(str(resp))
#     sys.exit(0)
#
# if args.command == 'get-job-script':
#     resp = api.get_job_script(args.get_job_script_id)
#     sys.stdout.write(str(resp))
#     sys.exit(0)
#
# if args.command == 'update-job-script':
#     resp = api.update_job_script(args.update_job_script_id)
#     sys.stdout.write(str(resp))
#     sys.exit(0)
#
# if args.command == 'delete-job-script':
#     resp = api.delete_job_script(args.delete_job_script_id)
#     sys.stdout.write(str(resp))
#     sys.exit(0)
#
# # Job Submissions
# if args.command == 'list-job-submissions':
#     resp = api.list_job_submissions()
#     sys.stdout.write(str(resp))
#     sys.exit(0)
#
# if args.command == 'create-job-submission':
#     resp = api.create_job_submission(
#         args.create_job_submission_name,
#         args.create_job_submission_job_script_id
#     )
#     sys.stdout.write(str(resp))
#     sys.exit(0)
#
# if args.command == 'get-job-submission':
#     resp = api.get_job_submission(args.get_job_submission_id)
#     sys.stdout.write(str(resp))
#     sys.exit(0)
#
# if args.command == 'update-job-submission':
#     resp = api.update_job_submission(args.update_job_submission_id)
#     sys.stdout.write(str(resp))
#     sys.exit(0)
#
# if args.command == 'delete-job-submission':
#     resp = api.delete_job_submission(args.delete_job_submission_id)
#     sys.stdout.write(str(resp))
#     sys.exit(0)
#
# # Applications
#

