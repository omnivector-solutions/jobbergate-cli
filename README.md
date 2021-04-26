# Jobbergate CLI
Jobbergate CLI client



## Usage
```bash
jobbergate --help
```

### It is possible to use raw sbatch parameters in create-job-script
Use the `--sbatch-params` multiple times to use as many parameters as needed in the following format
```bash
jobbergate create-job-script --sbatch-params='-N 10' --sbatch-params='--comment=some_comment'
```

## Release Process & Criteria

1. All automated tests pass on main through Github Actions
    - lint
    - unit tests, including coverage
    - snap builds successfully and uploads
    - system tests (2020-12-07 none currently exist, TBD)

    Continue to check automated tests at every step and commit; they must be green before release.

1. Prepare a release branch with a new version.

1. With
    ```bash
    JOBBERGATE_API_ENDPOINT=https://jobbergate-api-staging.omnivector.solutions
    ```

    Run the following tests:
    - `jobbergate --version` (confirm new version number)
    - `create-application`
    - `create-job-script`
    - `create-job-submission`
    - `update-application`
    - `update-job-script`
    - `update-job-submission`
    - `list-job-submissions`

    (FIXME: most of the above should be covered by automated system tests.)

1. Publish release branch to a production channel. These artifacts are needed:
    - snap in stable channel
    - release notes with change list (sent to ??? TBD)

    _n.b._ charm is a separate project and may not need to be updated.


## License
* [MIT](LICENSE)

## Copyright
* Copyright (c) 2020 OmniVector Solutions <admin@omnivector.solutions>
