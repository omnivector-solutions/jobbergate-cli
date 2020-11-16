from setuptools import setup, find_packages


setup(
    name='jobbergate-cli',
    packages=find_packages(include=['jobbergate_cli']),
    version='0.0.1',
    license='MIT',
    long_description=open('README.md').read(),
    install_requires=[
        'click',
        'inquirer',
        'pyjwt',
        'requests',
        'tabulate',
        'urllib3',
        'pyyaml',
    ],
    extras_require={
        'dev': [
            'coverage',
            'pytest',
            'pytest-cov',
            'tox',
            'wheel',
        ],
    },
    # data_files=[('config', ['config/*.json'])],
    entry_points = {
        'console_scripts': ['jobbergate-cli=jobbergate_cli.main:main'],
    }
)
