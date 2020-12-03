from setuptools import find_packages, setup


setup(
    name="jobbergate-cli",
    packages=find_packages(include=["jobbergate_cli", "jobbergate_cli.*"]),
    version="0.0.1+dev",
    license="MIT",
    long_description=open("README.md").read(),
    install_requires=[
        "click",
        # required for click.version_option()
        "importlib_metadata ; python_version < '3.8'",
        "inquirer",
        "pyjwt",
        "pyyaml",
        "requests",
        "tabulate",
        "urllib3",
    ],
    extras_require={
        "dev": [
            "black",
            "coverage",
            "flake8",
            "isort",
            "pytest",
            "pytest-cov",
            "pytest-freezegun",
            "pytest-responsemock",
            "tox",
            "wheel",
        ],
    },
    # data_files=[('config', ['config/*.json'])],
    entry_points={
        "console_scripts": ["jobbergate=jobbergate_cli.main:main"],
    },
)
