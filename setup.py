from setuptools import setup, find_packages

raw_reqs = open("requirements/requirements.txt", "r").read().splitlines()

setup(
    name='jobbergate-cli',
    packages=find_packages(include=['jobbergate_cli']),
    version='0.0.1',
    license='MIT',
    long_description=open('README.md').read(),
    install_requires=raw_reqs,
    entry_points = {
        'console_scripts': ['jobbergate-cli=jobbergate_cli.main:main'],
    }
)
