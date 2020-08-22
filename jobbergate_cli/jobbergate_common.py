import os
import urllib3
from pathlib import Path


JOBBERGATE_USER_TOKEN_DIR = Path(f"{str(Path.home())}/.local/cache/jobbergate")

JOBBERGATE_API_JWT_PATH = JOBBERGATE_USER_TOKEN_DIR / "jobbergate.token"

JOBBERGATE_API_ENDPOINT = "https://jobbergate-api-production.omnivector.solutions"
# JOBBERGATE_API_ENDPOINT = "http://0.0.0.0:8000"

JOBBERGATE_API_OBTAIN_TOKEN_ENDPOINT = f"{JOBBERGATE_API_ENDPOINT}/api-token-auth/"

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

MODULE_PATH = "/tmp/application.py"

CONFIG_PATH = "/tmp/jobbergate.yaml"

MODULE_NAME = ""
