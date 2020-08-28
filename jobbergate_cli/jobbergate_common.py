import os
import urllib3
from pathlib import Path


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

JOBBERGATE_CACHE_DIR = Path.home() / ".jobbergate"

JOBBERGATE_USER_TOKEN_DIR = JOBBERGATE_CACHE_DIR / "token"

JOBBERGATE_API_JWT_PATH = JOBBERGATE_USER_TOKEN_DIR / "jobbergate.token"

JOBBERGATE_CACHE_DIR = Path.home() / ".jobbergate"

JOBBERGATE_API_ENDPOINT = "https://jobbergate-api-production.omnivector.solutions"

JOBBERGATE_USER_TOKEN_DIR = JOBBERGATE_CACHE_DIR / "token"

JOBBERGATE_API_JWT_PATH = JOBBERGATE_USER_TOKEN_DIR / "jobbergate.token"

JOBBERGATE_API_OBTAIN_TOKEN_ENDPOINT = f"{JOBBERGATE_API_ENDPOINT}/api-token-auth/"

JOBBERGATE_APPLICATION_S3_BASE_PATH = "jobbergate-resources"



JOBBERGATE_APPLICATION_CONFIG = {
    "application_name": "",
    "application_description": "",
    "application_location": "TEST_LOC",
    "application_dir_listing": "",
    "application_dir_listing_acquired": True,
    "application_owner": ""
}

JOBBERGATE_JOB_SCRIPT_CONFIG = {
    "job_script_name": "",
    "job_script_description": "TEST_DESC",
    "job_script_data_as_string": "TEST_DATA_AS_STR",
    "job_script_owner": "",
    "application": ""
}

JOBBERGATE_JOB_SUBMISSION_CONFIG = {
    "job_submission_name": "",
    "job_submission_description": "TEST_DESC",
    "job_submission_owner": "",
    "job_script": ""
}

JOBBERGATE_APPLICATION_MODULE_FILE_NAME = "jobbergate.py"

JOBBERGATE_APPLICATION_CONFIG_FILE_NAME = "jobbergate.yaml"

JOBBERGATE_APPLICATION_MODULE_PATH = \
    JOBBERGATE_CACHE_DIR / JOBBERGATE_APPLICATION_MODULE_FILE_NAME

JOBBERGATE_APPLICATION_CONFIG_PATH = \
    JOBBERGATE_CACHE_DIR / JOBBERGATE_APPLICATION_CONFIG_FILE_NAME

TAR_NAME = "jobbergate.tar.gz"

JOBBERGATE_APPLICATION_MODULE_PATH = \
    JOBBERGATE_CACHE_DIR / JOBBERGATE_APPLICATION_MODULE_FILE_NAME

JOBBERGATE_APPLICATION_CONFIG_PATH = \
    JOBBERGATE_CACHE_DIR / JOBBERGATE_APPLICATION_CONFIG_FILE_NAME
