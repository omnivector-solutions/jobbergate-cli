============
 Change Log
============

This file keeps track of all notable changes to jobbergate-cli

Unreleased
----------
* Improved error handling on login
* Fixed requiring input for both username and password when one of them was already provided.
* Fixed the descripition for the option --update-identifier for update-application.
* Fixed application_id was not recovered at update-application when the user selected the application by its identifier.
* Fixed application_file and application_config, because the columns were not updated in the back-end when updating the application.

1.2.0 -- 2021-12-06
-------------------
- Added server-side filtering for list-* sub-commands

1.1.1 -- 2021-11-08
-------------------
- Removed leftover debug exception to fix ``list-applications`` command

1.1.0 -- 2021-11-05
-------------------
- Fixed bug for getting job_script name from params
- Added Sentry integration
- Added logging in user space and ability to upload logs to S3
- Added release scripts
- Converted to using poetry for dependencies and publishing
- Added targets in makefile
