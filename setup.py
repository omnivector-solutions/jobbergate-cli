from setuptools import setup, find_packages

raw_reqs = open("requirements/requirements.txt", "r").read().splitlines()

setup(
    name='jobbergate-cli',
    packages=find_packages(include=['*']),
    version='0.0.1',
    license='MIT',
    long_description=open('README.md').read(),
    install_requires=install_reqs,
    entry_points = {
        'console_scripts': ['jobbergate-cli=jobbergate_cli.main:main'],
    }
)
