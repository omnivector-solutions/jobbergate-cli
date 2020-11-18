from setuptools import find_packages, setup


setup(
    name="jobbergate-cli",
    packages=find_packages(include=["jobbergate_cli"]),
    version="0.0.1+dev",
    license="MIT",
    long_description=open("README.md").read(),
    install_requires=[
        "click",
        "inquirer",
        "pyjwt",
        "requests",
        "tabulate",
        "urllib3",
        "pyyaml",
    ],
    extras_require={
        "dev": [
            "black",
            "coverage",
            "flake8",
            "isort",
            "pytest",
            "pytest-cov",
            "tox",
            "wheel",
        ],
    },
    # data_files=[('config', ['config/*.json'])],
    entry_points={
        "console_scripts": ["jobbergate=jobbergate_cli.main:main"],
    },
)
