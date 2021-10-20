import os
from pathlib import Path
import subprocess


def get_running_jobs(user_only=True):
    """Returns a list of the user's currently running jobs, as given by SLURM."""
    cmd_args = [
        "squeue",
        '--format="%.8A %j"',
        "--noheader",
    ]  # format:[job ID, 8 chars] [job name]
    if user_only:
        cmd_args.append("--user=" + os.getenv("USER"))
    try:
        cmd_results = subprocess.run(cmd_args, stdout=subprocess.PIPE)
        # Skip last line (empty), strip quotation marks
        ID_alternatives = cmd_results.stdout.decode().split("\n")[:-1]
        ID_alternatives = [j.strip('"') for j in ID_alternatives]
    except:  # noqa: E722
        print("Could not retrieve queue information from SLURM.")
        return []
    return ID_alternatives


def get_file_list(path=None, search_term="*.*"):
    """Returns a list of input files in a directory ( default: pwd)."""
    if not path:
        path = Path.cwd()

    files = sorted(path.glob(search_term), key=os.path.getmtime, reverse=True)

    files = [x.name for x in files if x.is_file()]

    return files
