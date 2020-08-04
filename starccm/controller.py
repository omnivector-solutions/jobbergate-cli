import os
from jinja2 import Environment, FileSystemLoader

from jobbergate import workflow
from jobberapplications.lib.jobberappslib import get_output_file

@workflow.logic
def pre_(data):
    retval = {}
    retval["scriptout"] = get_output_file()
    retval["answers"] = []
    return retval

@workflow.logic
def pre_Sim(data):
    retval = {}
    retval["partition"]="centos"
    retval["nextworkflow"] = "wrapup"
    return retval

@workflow.logic
def pre_Mesh(data):
    retval = {}
    retval["partition"]="highfreq"
    retval["nextworkflow"] = "wrapup"
    return retval

@workflow.logic
def pre_Parallel(data):
    retval = {}
    retval["partition"]="highfreq"
    retval["nextworkflow"] = "wrapup"
    return retval

@workflow.logic
def pre_PostMeshNode(data):
    retval = {}
    retval["partition"]="highfreq"
    retval["nextworkflow"] = "wrapup"
    return retval

@workflow.logic
def pre_PostComputeNode(data):
    retval = {}
    retval["partition"]="centos"
    retval["nextworkflow"] = "wrapup"
    return retval

@workflow.logic
def pre_Cosim(data):
    retval = {}
    retval["partition"]="centos"
    retval["nextworkflow"] = "wrapup"
    return retval

@workflow.logic
def pre_PostVTM(data):
    retval = {}
    retval["partition"]="highfreq"
    retval["nextworkflow"] = "wrapup"
    return retval

@workflow.logic
def post_mainflow(data):
    retval = {}
    # Answers = what to list at end of script to be able to reproduce
    retval["answers"] = ["cluster", "module", "filename", "workflow", "timelimit", "cores", "jobname"]
    retval["nextworkflow"] = "shared" # All flows continue here

    # Special template for Beskow jobs
    if data["cluster"] == "Beskow":
        retval["template"] = data["beskow_template"]
    return retval

@workflow.logic
def post_shared(data):
    retval = {}
    retval["nextworkflow"] = data["workflow"]
    return retval

@workflow.logic
def post_Sim(data):
    retval = {}
    # Default core amount
    if data["cores"] == "":
        retval["cores"] = 64
    data["answers"].extend(["user_dependencies", "other_dependencies", "simsteps"])
    return retval

@workflow.logic
def post_Mesh(data):
    retval = {}
    # Default core amount
    if data["cores"] == "":
        retval["cores"] = 1
    data["answers"].extend(["memory"])
    return retval

@workflow.logic
def post_PostMeshNode(data):
    retval = {}
    # Default core amount
    if data["cores"] == "":
        retval["cores"] = 40
    data["answers"].extend(["memory", "sharenode"])
    return retval

@workflow.logic
def post_PostVTM(data):
    retval = {}
    # Default core amount
    if data["cores"] == "":
        retval["cores"] = 16
    data["answers"].extend(["memory"])
    return retval

@workflow.logic
def post_wrapup(data):
    retval = {}
    data["answers"].extend(["stageup", "submitnow"])
    return retval

@workflow.logic
def post_(data):
    retval = {}
    # Combine dependencies
    all_dependencies=[]
    if "user_dependencies" in data.keys():
        all_dependencies = data["user_dependencies"]
    if "other_dependencies" in data.keys() and data["other_dependencies"] != "":
        all_dependencies.extend(data["other_dependencies"].split(":"))
    if all_dependencies != []:
        retval["all_dependencies"] = all_dependencies
    # Console command if any
    if data["submitnow"]:
        retval["cmd_command"] = f"sbatch {data['scriptout']}"

    # Create Java start macro
    with open(f"starccm{data['workflow']}.java","w") as javafile:
        templatedir=os.path.join(data["jobbergateconfig"]["apps"]["path"], "starccm/templates/")
        javatemplate = Environment(loader=FileSystemLoader(templatedir)).get_template("java-generic-template.j2") #TODO un-hardcode
        javafile.write(javatemplate.render(data=data))

    return retval
