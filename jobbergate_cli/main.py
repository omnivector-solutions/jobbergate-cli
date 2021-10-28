#!/usr/bin/env python3
from datetime import datetime
import functools
import getpass
from pathlib import Path
import sys
import tarfile
import tempfile
import textwrap

import boto3
import click
import jwt
from loguru import logger
import requests
import sentry_sdk

from jobbergate_cli import client
from jobbergate_cli.jobbergate_api_wrapper import JobbergateApi
from jobbergate_cli.jobbergate_common import (
    JOBBERGATE_API_ENDPOINT,
    JOBBERGATE_API_JWT_PATH,
    JOBBERGATE_API_OBTAIN_TOKEN_ENDPOINT,
    JOBBERGATE_APPLICATION_CONFIG,
    JOBBERGATE_AWS_ACCESS_KEY_ID,
    JOBBERGATE_AWS_SECRET_ACCESS_KEY,
    JOBBERGATE_CACHE_DIR,
    JOBBERGATE_DEBUG,
    JOBBERGATE_JOB_SCRIPT_CONFIG,
    JOBBERGATE_JOB_SUBMISSION_CONFIG,
    JOBBERGATE_LOG_PATH,
    JOBBERGATE_PASSWORD,
    JOBBERGATE_S3_LOG_BUCKET,
    JOBBERGATE_USER_TOKEN_DIR,
    JOBBERGATE_USERNAME,
    SENTRY_DSN,
)


# These are used in help text for the application commands below
APPLICATION_ID_EXPLANATION = """

    This id represents the primary key of the application in the database. It
    will always be a unique integer. All applications receive an id, so it may
    be used to target a specific instance of an application whether or not it
    is provided with a human-friendly "identifier".
"""


APPLICAITON_IDENTIFIER_EXPLANATION = """

    The identifier allows the user to access commonly used applications with a
    friendly name that is easy to remember. Identifiers should only be used
    for applicaitons that are frequently used or should be easy to find in the list.
"""


class Api(object):
    def __init__(self, user_id=None):
        logger.debug("Initializing JobbergateApi")
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


def init_cache_dir():
    """
    Make sure that the root Jobbergate cache directory exists.
    """
    JOBBERGATE_CACHE_DIR.mkdir(exist_ok=True, parents=True)


def init_logs(username=None, verbose=False):
    """
    Initialize the rotatating file log handler. Logs will be retained for 1 week.
    """
    # Remove default stderr handler at level INFO
    logger.remove()
    JOBBERGATE_LOG_PATH.parent.mkdir(exist_ok=True)

    if verbose:
        logger.add(sys.stdout, level="DEBUG")

    logger.add(JOBBERGATE_LOG_PATH, rotation="00:00", retention="1 week", level="DEBUG")
    logger.debug("Logging initialized")
    if username:
        logger.debug(f"  for user {username}")


def jobbergate_command_wrapper(func):
    """Wraps a jobbergate command to include logging, error handling, and user output

    Reports the command being called an its parameters to the user log. Includes log
    lines about starting and finishing the command. Also reports errors to the user
    as well as sending the error report to Sentry. Finally, prints any output provided
    by the called command to stdout.
    """

    @functools.wraps(func)
    def wrapper(ctx, *args, **kwargs):
        try:
            main_message = f"Handling command '{ctx.command.name}'"
            if ctx.params:
                main_message += " with params:"
            logger.debug(
                "\n  ".join(
                    [main_message, *[f"{k}={v}" for (k, v) in ctx.params.items()]]
                )
            )

            result = func(ctx, *args, **kwargs)
            if result:
                print(result)
            return result

        except Exception as err:
            message = "Caught error for {user} ({id_}) in {fn}({args_string})".format(
                user=ctx.obj["token"]["username"],
                id_=ctx.obj["token"]["user_id"],
                fn=func.__name__,
                args_string=", ".join(
                    list(args) + [f"{k}={v}" for (k, v) in kwargs.items()]
                ),
            )
            logger.error(message)

            # This allows us to capture exceptions here and still report them to sentry
            if SENTRY_DSN:
                with sentry_sdk.push_scope() as scope:
                    scope.set_context(
                        "command_info",
                        dict(
                            username=ctx.obj["token"]["username"],
                            user_id=ctx.obj["token"]["user_id"],
                            function=func.__name__,
                            command=ctx.command.name,
                            args=args,
                            kwargs=kwargs,
                        ),
                    )
                    sentry_sdk.capture_exception(err)
                    sentry_sdk.flush()

            print(
                textwrap.dedent(
                    f"""
                    There was an error processing command '{ctx.command.name}'.

                    Please check the parameters and the command documentation. You can check the documentation
                    at any time by adding '--help' to any command.

                    If the problem persists, please contact Omnivector <info@omnivector.solutions> for support.
                    """
                ).strip()
            )

        finally:
            logger.debug(f"Finished command '{ctx.command.name}'")

    return wrapper


def init_token(username, password):
    """Get a new token from the api and write it to the token file."""
    logger.debug(f"Initializing auth token for {username}")
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
        logger.error(f"Invalid token: {e}")
        # FIXME - raise an exception (and catch, then ctx.exit())
        sys.exit()
    return token


def init_api(user_id):
    """Initialize the API for the user's session."""
    logger.debug("Initializing Jobbergate API.")
    api = JobbergateApi(
        token=JOBBERGATE_API_JWT_PATH.read_text(),
        job_script_config=JOBBERGATE_JOB_SCRIPT_CONFIG,
        job_submission_config=JOBBERGATE_JOB_SUBMISSION_CONFIG,
        application_config=JOBBERGATE_APPLICATION_CONFIG,
        api_endpoint=JOBBERGATE_API_ENDPOINT,
        user_id=user_id,
    )
    return api


def init_sentry():
    """Initialize Sentry."""
    logger.debug("Initializing sentry")
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
    )


# Get the cli input arguments
# args = get_parsed_args(argv)


# def get_parsed_args(argv):
"""Create argument parser and return cli args.
"""


# Get the cli input arguments
@click.group(
    help=f"""
        Jobbergate CLI.

        Provides a command-line interface to the Jobbergate API. Available commands are
        listed below. Each command may be invoked with --help to see more details and
        available parameters.

        If you have not logged in before and you do not include the --username and
        --password options, you will be prompted for your login info. You may also supply
        your username and password through the environment variables JOBBERGATE_USERNAME
        and JOBBERGATE_PASSWORD.

        Once your username and password have been authenticated, an auth token is issued by
        the backend. This token is securely saved locally ({JOBBERGATE_USER_TOKEN_DIR})
        and attached to the requests issued in subsequent commands so you do not need to
        supply your credentials every time. After some time, the auth token will expire and
        you will need to supply your username and password again.
    """,
)
@click.option(
    "--username",
    "-u",
    default=JOBBERGATE_USERNAME,
    help="Your Jobbergate API Username",
)
@click.option(
    "--password",
    "-p",
    default=JOBBERGATE_PASSWORD,
    help="Your Jobbergate API password",
    hide_input=True,
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging to the terminal",
)
@click.version_option()
@click.pass_context
def main(ctx, username, password, verbose):
    ctx.ensure_object(dict)

    init_cache_dir()
    init_logs(username=username, verbose=verbose)

    if SENTRY_DSN:
        logger.debug(f"Initializing Sentry with {SENTRY_DSN}")
        init_sentry()

    # create dir for token if it doesnt exist
    Path(JOBBERGATE_USER_TOKEN_DIR).mkdir(parents=True, exist_ok=True)

    if JOBBERGATE_DEBUG:
        client.debug_requests_on()

    if not is_token_valid():
        logger.debug("Token is not valid. Getting credentials.")
        if username and password:
            logger.debug(f"Logging in with command-line credentials for {username}")
            ctx.obj["username"] = username
            ctx.obj["password"] = password
        else:
            logger.debug("Getting credentials from interactive prompt")
            username, password = interactive_get_username_password()
            logger.debug(f"Logging in with interactive credentials for {username}")
            ctx.obj["username"] = username
            ctx.obj["password"] = password

        try:
            logger.debug(f"Initializing token for {username}")
            init_token(username, password)
        except requests.exceptions.ConnectionError as err:
            message = f"Auth failed to establish connection with API: {str(err)}"
            sentry_sdk.capture_message(message)
            logger.error(f"{message}")
            raise click.ClickException(
                "Couldn't verify login to the server due to communications problem. Please try again.",
            )
        except Exception as err:
            logger.error(f"Auth Failed for '{username}': {str(err)}")
            raise click.ClickException(f"Failed to login with '{username}'. Please try again.")

    logger.debug("Decoding auth token")
    ctx.obj["token"] = decode_token_to_dict(JOBBERGATE_API_JWT_PATH.read_text())
    username = ctx.obj["token"]["username"]
    user_id = ctx.obj["token"]["user_id"]
    logger.debug(f"User invoking jobbergate-cli is {username} ({user_id})")
    ctx.obj["api"] = JobbergateApi(
        token=JOBBERGATE_API_JWT_PATH.read_text(),
        job_script_config=JOBBERGATE_JOB_SCRIPT_CONFIG,
        job_submission_config=JOBBERGATE_JOB_SUBMISSION_CONFIG,
        application_config=JOBBERGATE_APPLICATION_CONFIG,
        api_endpoint=JOBBERGATE_API_ENDPOINT,
        user_id=user_id,
    )


@main.command("list-applications")
@click.option(
    "--all",
    is_flag=True,
    help="Show all applications, even the ones without identifier",
)
@click.option(
    "--user",
    is_flag=True,
    help="Show only the applications for the current user",
)
@click.pass_context
@jobbergate_command_wrapper
def list_applications(ctx, all=False, user=False):
    """
    LIST the available applications.
    """
    api = ctx.obj["api"]
    return api.list_applications(all, user)


@main.command("create-application")
@click.option("--name", "-n", help="Name of the application")
@click.option(
    "--identifier",
    help=f"The human-friendly identifier of the application. {APPLICAITON_IDENTIFIER_EXPLANATION}",
)
@click.option(
    "--application-path",
    "-a",
    help="The path to the directory where application files are",
)
@click.option(
    "--application-desc",
    default="",
    help="A helpful description of the application",
)
@click.pass_context
@jobbergate_command_wrapper
def create_application(
    ctx,
    name,
    identifier,
    application_path,
    application_desc,
):
    """
    CREATE an application.
    """
    api = ctx.obj["api"]
    return api.create_application(
        application_name=name,
        application_identifier=identifier,
        application_path=application_path,
        application_desc=application_desc,
    )


@main.command("get-application")
@click.option(
    "--id",
    "-i",
    "id_",
    help=f"The specific id of the application. {APPLICATION_ID_EXPLANATION}",
)
@click.option(
    "--identifier",
    help=f"The human-friendly identifier of the application. {APPLICAITON_IDENTIFIER_EXPLANATION}",
)
@click.pass_context
@jobbergate_command_wrapper
def get_application(ctx, id_, identifier):
    """
    GET an Application.
    """
    api = ctx.obj["api"]
    return api.get_application(application_id=id_, application_identifier=identifier)


@main.command("update-application")
@click.option(
    "--id",
    "-i",
    "id_",
    help=f"The specific id application to update. {APPLICATION_ID_EXPLANATION}",
)
@click.option(
    "--identifier",
    help=f"The human-friendly identifier of the application to update. {APPLICAITON_IDENTIFIER_EXPLANATION}",
)
@click.option(
    "--application-path",
    "-a",
    help="The path to the directory for updated application files",
)
@click.option("--update-identifier", help="The application identifier to be set")
@click.option(
    "--application-desc",
    default="",
    help="Optional new application description",
)
@click.pass_context
@jobbergate_command_wrapper
def update_application(
    ctx,
    id_,
    identifier,
    application_path,
    update_identifier,
    application_desc,
):
    """
    UPDATE an Application.
    """
    api = ctx.obj["api"]
    return api.update_application(id_, identifier, application_path, update_identifier, application_desc)


@main.command("delete-application")
@click.option(
    "--id",
    "-i",
    "id_",
    help=f"The specific id of the application to delete. {APPLICATION_ID_EXPLANATION}",
)
@click.option(
    "--identifier",
    help=f"The human-friendly identifier of the application to delete. {APPLICAITON_IDENTIFIER_EXPLANATION}",
)
@click.pass_context
@jobbergate_command_wrapper
def delete_application(ctx, id_, identifier):
    """
    DELETE an Application.
    """
    api = ctx.obj["api"]
    return api.delete_application(id_, identifier)


@main.command("list-job-scripts")
@click.option(
    "--all",
    "all_",
    is_flag=True,
    help="""
        Optional parameter that will return all job scripts.
        If NOT specified then only the user's job scripts will be returned.
    """,
)
@click.pass_context
@jobbergate_command_wrapper
def list_job_scripts(ctx, all_=False):
    """
    LIST Job Scripts.
    """
    api = ctx.obj["api"]
    return api.list_job_scripts(all_)


@main.command("create-job-script")
@click.option(
    "--name",
    "-n",
    default="default_script_name",
    help="Name for job script",
)
@click.option(
    "--application-id",
    "-i",
    help="The id of the application for the job script",
)
@click.option(
    "--application-identifier",
    help="The identifier of the application for the job script",
)
@click.option(
    "--sbatch-params",
    multiple=True,
    help="Optional parameter to submit raw sbatch parameters",
)
@click.option(
    "--param-file",
    type=click.Path(),
    help="""
        Optional parameter file for populating templates.
        If answers are not provided, the question asking in jobbergate.py is triggered
    """,
)
@click.option(
    "--fast",
    "-f",
    is_flag=True,
    help="""
        Optional parameter to use default answers (when available)
        instead of asking user.
    """,
)
@click.option(
    "--no-submit",
    is_flag=True,
    help="Optional parameter to not even ask about submitting job",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Optional parameter to view job script data in CLI output",
)
@click.pass_context
@jobbergate_command_wrapper
def create_job_script(
    ctx,
    name,
    application_id,
    application_identifier,
    sbatch_params,
    param_file=None,
    fast=False,
    no_submit=False,
    debug=False,
):
    """
    CREATE a Job Script.
    """
    api = ctx.obj["api"]
    return api.create_job_script(
        name,
        application_id,
        application_identifier,
        param_file,
        sbatch_params,
        fast,
        no_submit,
        debug,
    )


@main.command("get-job-script")
@click.option(
    "--id",
    "-i",
    "id_",
    help="The id of job script to be returned",
)
@click.option(
    "--as-string",
    is_flag=True,
)
@click.pass_context
@jobbergate_command_wrapper
def get_job_script(ctx, id_, as_string):
    """
    GET a Job Script.
    """
    api = ctx.obj["api"]
    return api.get_job_script(id_, as_string)


@main.command("update-job-script")
@click.option(
    "--id",
    "-i",
    "id_",
    help="The id of the job script to update",
)
@click.option(
    "--job-script",
    help="""
        The data with which to update job script.

        Format: string form of dictionary with main script as entry "application.sh"

        Example: '{"application.sh":"#!/bin/bash \\n hostname"}'
    """,
)
@click.pass_context
@jobbergate_command_wrapper
def update_job_script(ctx, id_, job_script):
    """
    UPDATE a Job Script.
    """
    api = ctx.obj["api"]
    return api.update_job_script(id_, job_script)


@main.command("delete-job-script")
@click.option("--id", "-i", "id_", help="The id of job script to delete")
@click.pass_context
@jobbergate_command_wrapper
def delete_job_script(ctx, id_):
    """
    DELETE a Job Script.
    """
    api = ctx.obj["api"]
    return api.delete_job_script(id_)


@main.command("list-job-submissions")
@click.option(
    "--all",
    "all_",
    is_flag=True,
    help="""
        Optional parameter that will return all job submissions.
        If NOT specified then only the user's job submissions will be returned.
    """,
)
@click.pass_context
@jobbergate_command_wrapper
def list_job_submissions(ctx, all_=False):
    """
    LIST Job Submissions.
    """
    api = ctx.obj["api"]
    return api.list_job_submissions(all_)


@main.command("create-job-submission")
@click.option(
    "--job-script-id",
    "-i",
    help="The id of the job script to submit",
)
@click.option(
    "--name",
    "-n",
    help="The name for job submission",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="""
        Optional flag that will create record in API and return data to CLI but
        WILL NOT submit job
    """,
)
@click.pass_context
@jobbergate_command_wrapper
def create_job_submission(
    ctx,
    job_script_id,
    name="",
    dry_run=False,
):
    """
    CREATE Job Submission.
    """
    api = ctx.obj["api"]
    return api.create_job_submission(job_script_id=job_script_id, job_submission_name=name, render_only=dry_run)


@main.command("get-job-submission")
@click.option("--id", "-i", "id_", help="The id of the job submission to be returned")
@click.pass_context
@jobbergate_command_wrapper
def get_job_submission(ctx, id_):
    """
    GET a Job Submission.
    """
    api = ctx.obj["api"]
    return api.get_job_submission(id_)


@main.command("update-job-submission")
@click.option("--id", "-i", "id_", help="The id of job submission to update")
@click.pass_context
@jobbergate_command_wrapper
def update_job_submission(ctx, id_):
    """
    UPDATE a Job Submission.
    """
    api = ctx.obj["api"]
    return api.update_job_submission(id_)


@main.command("delete-job-submission")
@click.option("--id", "-i", "id_", help="The id of job submission to delete")
@click.pass_context
@jobbergate_command_wrapper
def delete_job_submission(ctx, id_):
    """
    DELETE a Job Submission.
    """
    api = ctx.obj["api"]
    return api.delete_job_submission(id_)


@main.command("upload-logs")
@click.pass_context
@jobbergate_command_wrapper
def upload_logs(ctx):
    """
    Uploads user logs to S3 for analysis. Should only be used after an incident that was
    reported to the Jobbergate support team.
    """
    logger.debug("Initializing S3 client")
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=JOBBERGATE_AWS_ACCESS_KEY_ID,
        aws_secret_access_key=JOBBERGATE_AWS_SECRET_ACCESS_KEY,
    )

    tarball_name = "{user}.{timestamp}.tar.gz".format(
        user=ctx.obj["token"]["username"],
        timestamp=datetime.utcnow().strftime("%Y%m%d.%H%M%S"),
    )

    logger.debug("Creating tarball of user's logs")
    log_dir = JOBBERGATE_LOG_PATH.parent
    with tempfile.TemporaryDirectory() as temp_dir:
        tarball_path = Path(temp_dir) / tarball_name
        with tarfile.open(tarball_path, "w:gz") as tarball:
            for filename in log_dir.iterdir():
                if filename.match(f"{JOBBERGATE_LOG_PATH}*"):
                    tarball.add(str(filename))

        logger.debug(f"Uploading {tarball_name} to S3")
        s3_client.upload_file(str(tarball_path), JOBBERGATE_S3_LOG_BUCKET, tarball_name)

    return "Upload complete. Please notify Omnivector <info@omnivector.solution>."


@main.command("logout")
@click.pass_context
@jobbergate_command_wrapper
def logout(ctx):
    """
    Logs out of the jobbergate-cli. Clears the saved user credentials.
    """
    if not JOBBERGATE_API_JWT_PATH.exists():
        logger.debug("No user is currently logged in")
    else:
        JOBBERGATE_API_JWT_PATH.unlink()
        logger.debug("Cleared saved auth token")


if __name__ == "__main__":
    main()
