import os
import urllib3
from pathlib import Path

JOBBERGATE_USER_TOKEN_DIR = f"{str(Path.home())}/.local/cache/jobbergate-cli"

JOBBERGATE_API_JWT_PATH = Path(f"{JOBBERGATE_USER_TOKEN_DIR}/jobbergate.token")


JOBBERGATE_API_ENDPOINT = "https://jobbergate-api-production.omnivector.solutions"
# JOBBERGATE_API_ENDPOINT = "http://0.0.0.0:8000"

JOBBERGATE_API_OBTAIN_TOKEN_ENDPOINT = f"{JOBBERGATE_API_ENDPOINT}/api-token-auth/"

dir_path = os.path.dirname(os.path.realpath(__file__))

JOBBERGATE_APPLICATION_BASE_PATH = "jobbergate-resources"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

APPLICATION_CONFIG = {
    "application_name": "",
    "application_description": "TEST_DESC",
    "application_location": "TEST_LOC",
    "application_dir_listing": "TEST_DIR_LISTING",
    "application_dir_listing_acquired": True,
    "application_owner": ""
}

JOB_SCRIPT_CONFIG = {
    "job_script_name": "",
    "job_script_description": "TEST_DESC",
    "job_script_data_as_string": "TEST_DATA_AS_STR",
    "job_script_owner": "",
    "application": ""
}

JOB_SUBMISSION_CONFIG = {
    "job_submission_name": "",
    "job_submission_description": "TEST_DESC",
    "job_submission_owner": "",
    "job_script": ""
}

APPLICATION_FILENAME = "jobbergate.py"

CONFIG_FILENAME = "jobbergate.yaml"

MODULE_PATH = f"/tmp/{APPLICATION_FILENAME}"

CONFIG_PATH = f"/tmp/{CONFIG_FILENAME }"

MODULE_NAME = ""