#!/usr/bin/env python3
from argparse import ArgumentParser

from jobbergate_api_wrapper import JobbergateAPI


def get_parsed_args(argv):
    """Create argument parser and return cli args.
    """
    parser = ArgumentParser(
        description="Jobbergate CLI"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Jobbergate CLI Operations.",
    )

    # Applications
    list_applications_parser = subparsers.add_parser(
        "list-applications",
        help="List applications.",
    )

    create_application_parser = subparsers.add_parser(
        "create-application",
        help="Create an application.",
    )
    create_application_parser.add_argument(
        "-n",
        "--name",
        required=True,
        dest="create_application_name",
        help="Name of the application.",
    )

    get_application_parser = subparsers.add_parser(
        "get-application",
        help="Return an application.",
    )
    get_application_parser.add_argument(
        "-i",
        "--id",
        required=True,
        dest="get_application_id",
        help="Application id.",
    )

    update_application_parser = subparsers.add_parser(
        "update-application",
        help="Update an application.",
    )
    update_application_parser.add_argument(
        "-i",
        "--id",
        required=True,
        dest="update_application_id",
        help="Id of the desired application to update.",
    )

    delete_application_parser = subparsers.add_parser(
        "delete-application",
        help="Delete an application.",
    )
    delete_application_parser.add_argument(
        "-i",
        "--id",
        required=True,
        dest="delete_application_id",
        help="Id of the desired application to delete.",
    )

    # Job Scripts
    list_job_scripts_parser = subparsers.add_parser(
        "list-job-scripts",
        help="List job scripts.",
    )

    create_job_script_parser = subparsers.add_parser(
        "create-job-script",
        help="Create a job-script",
    )
    create_job_script_parser.add_argument(
        "-n",
        "--name",
        required=True,
        dest="create_job_script_name",
        help="Name of the job-script to create.",
    )

    get_job_script_parser = subparsers.add_parser(
        "get-job-script",
        help="Return a job-script",
    )
    get_job_script_parser.add_argument(
        "-i",
        "--id",
        required=True,
        dest="get_job_script_id",
        help="Id of the desired job script to return.",
    )

    update_job_script_parser = subparsers.add_parser(
        "update-job-script",
        help="Update a job-script",
    )
    update_job_script_parser.add_argument(
        "-i",
        "--id",
        required=True,
        dest="update_job_script_id",
        help="Id of the desired job script to update.",
    )

    delete_job_script_parser = subparsers.add_parser(
        "delete-job-script",
        help="Delete a job-script",
    )
    delete_job_script_parser.add_argument(
        "-i",
        "--id",
        required=True,
        dest="delete_job_script_id",
        help="Id of the desired job script to delete.",
    )

    # Job Submissions
    list_job_submissions_parser = subparsers.add_parser(
        "list-job-submissions",
        help="List job submissions.",
    )

    create_job_submission_parser = subparsers.add_parser(
        "create-job-submission",
        help="Create a job submission.",
    )
    create_job_submission_parser.add_argument(
        "-n",
        "--name",
        required=True,
        dest="create_job_submission_name",
        help="Name of the job submission.",
    )

    get_job_submission_parser = subparsers.add_parser(
        "get-job-submission",
        help="Return a job submission",
    )
    get_job_submission_parser.add_argument(
        "-i",
        "--id",
        required=True,
        dest="get_job_submission_id",
        help="Id of the desired job submission to return.",
    )

    update_job_submission_parser = subparsers.add_parser(
        "update-job-submission",
        help="Update a job submission.",
    )
    update_job_submission_parser.add_argument(
        "-i",
        "--id",
        required=True,
        dest="update_job_submission_id",
        help="Id of the desired job submission to update.",
    )

    delete_job_submission_parser = subparsers.add_parser(
        "delete-job-submission",
        help="Delete a job submission.",
    )
    delete_job_submission_parser.add_argument(
        "-i",
        "--id",
        required=True,
        dest="delete_job_submission_id",
        help="Id of the desired job submission to delete.",
    )

    return parser.parse_args(argv)


def main(argv=sys.argv[1:]):
    # Get the cli input arguments
    args = get_parsed_args(argv)

    # Try to use pre-existing token, if doesn't exist or invalid,
    # try to get a new one.
    # Allow the use to pass their jobbergate username and password as 
    # command line arguments. If a token isn't found and the username and password
    # are not supplied at runtime, we will launch an interactive
    # username password acquisition session.
    token = Path("/tmp/jobbergate.token")
    import jwt

    if token.exists():
        token = jwt.decode(
            token.read_text(),
            'secret',
            algorithms=['HS256']
        )

    if args.username and args.password:
        user_pass = {'username': args.username, 'password': args.password}
    else:
        user_pass = get_user_pass_interactive()

    api = JobbergateApi(**user_pass)

    # Job Scripts
    if args.command == 'list-job-scripts':
        resp = api.list_job_scripts()
        print(resp)
        sys.exit(0)

    if args.command == 'create-job-script':
        resp = api.create_job_script(
            args.create_job_script_name,
            args.create_job_script_application_id,
        )
        print(resp)
        sys.exit(0)

    if args.command == 'get-job-script':
        resp = api.get_job_script(args.get_job_script_id)
        print(resp)
        sys.exit(0)

    if args.command == 'update-job-script':
        resp = api.update_job_script(args.update_job_script_id)
        print(resp)
        sys.exit(0)

    if args.command == 'delete-job-script':
        resp = api.delete_job_script(args.get_job_script_id)
        print(resp)
        sys.exit(0)

    # Job Submissions
    if args.command == 'list-job-submissions':
        resp = api.list_job_submissions()
        print(resp)
        sys.exit(0)

    if args.command == 'create-job-submission':
        resp = api.create_job_submission(
            args.create_job_submission_name,
            args.create_job_submission_job_script_id
        )
        print(resp)
        sys.exit(0)

    if args.command == 'get-job-submission':
        resp = api.get_job_submission(args.get_job_submission_id)
        print(resp)
        sys.exit(0)

    if args.command == 'update-job-submission':
        resp = api.update_job_submission(args.update_job_submission_id)
        print(resp)
        sys.exit(0)

    if args.command == 'delete-job-submission':
        resp = api.delete_job_submission(args.delete_job_submission_id)
        print(resp)
        sys.exit(0)

    # Applications
    if args.command == 'list-applications':
        resp = api.list_applications()
        print(resp)
        sys.exit(0)

    if args.command == 'create-application':
        resp = api.create_application(args.create_application_name)
        print(resp)
        sys.exit(0)

    if args.command == 'get-application':
        resp = api.get_application(args.get_application_id)
        print(resp)
        sys.exit(0)

    if args.command == 'update-application':
        resp = api.update_application(args.update_application_id)
        print(resp)
        sys.exit(0)

    if args.command == 'delete-application':
        resp = api.delete_application(args.delete_application_id)
        print(resp)
        sys.exit(0)


if __name__ == "__main__":
    main()
