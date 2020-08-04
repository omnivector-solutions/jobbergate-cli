from jobbergate import appform
import os
from jobberapplications.lib.jobberappslib import get_running_jobs, get_file_list

# Tool to compare version strings
def _versionstring_to_num(key):
    value=""
    key = key.split("/")[1]
    for char in key:
        if char.isdigit(): # Add
            value+=char
        elif char == ".": # Ignore
            pass
        else:
            break # The rest is irrelevant
    return int(value)

def mainflow(data):
    questions = []
    questions.append(appform.List(
        "cluster",
        message="Choose which cluster to build script for",
        choices=[
            ("Nash (Scania)", "Nash"),
            ("Beskow (KTH)", "Beskow")]
    ))

    questions.append(appform.List(
        "workflow",
        message="Select simulation task",
        choices=[
            ("Simulate", "Sim"),
            ("Meshing",  "Mesh"),
            ("Mesh parallel",  "Parallel"),
            ("Postprocessing - mesh node",  "PostMeshNode"),
            ("Postprocessing - compute node", "PostComputeNode"),
            ("Co-simulate", "Cosim"),
            ("Postprocessing - VTM", "PostVTM")]
    ))

    return questions

def shared(data):
    questions = []
    if data["cluster"] == "Beskow":
        modules = data["beskow_available_versions"]
    else:
        #modules = [ "star/"+ver[1:] for ver in os.listdir(data["module_dir"]) if ver[0]=='v'] # TODO revert to this when modules are available on Nash nodes
        modules = [ "star-ccm+/"+ver[1:] for ver in os.listdir(data["module_dir"]) if ver[0]=='v']
        modules.sort(key=_versionstring_to_num, reverse=True)
    questions.append(appform.List(
        "module",
        message="Select STAR-CCM+ version",
        choices=modules
    ))

    input_files = get_file_list(search_term="*.sim")
    if not input_files:
        questions.append(appform.File(
            "filename",
            message="Input file (absolute path)",
            exists=True,
        ))
    else:
        questions.append(appform.List(
            "filename",
            message="Select .sim input file",
            choices=input_files
        ))

    questions.append(appform.List(
        "timelimit",
        message="Set maximum time (h)",
        choices=[1,2,4,6,8,16,24,48,72,96,144,192]
    ))

    if data["workflow"] == "Mesh": # No need to ask
        questions.append(appform.Const("cores",1))
    else:
        cores_per_node = {
            "Nash":40,
            "Beskow":36 # 32 for old hardware, still relevant?
        }
        default_cores={
            "Sim":280, # Cores per node * 7?
            "Mesh":1,
            "Parallel":cores_per_node[data['cluster']],
            "PostMeshNode":cores_per_node[data['cluster']],
            "Cosim":280,
            "PostVTM":16
        }
        questions.append(appform.Integer(
            "cores",
            message=f"Amount of cores ({cores_per_node[data['cluster']]} per node)",
            default=default_cores[data["workflow"]]
        ))

    questions.append(appform.Text(
        "jobname",
        message="Name of job"
    ))
    return questions

def Sim(data):
    questions=[]
    possible_jobs= get_running_jobs()
    if(possible_jobs == []):
        print("You have no active jobs to wait for.")
        questions.append(appform.Const("user_dependencies", []))
    else:
        # (Display name, value)
        ID_alternatives = [(j, j.strip().split(" ")[0]) for j in possible_jobs]
        questions.append(appform.Checkbox(
            "user_dependencies",
            message="Select all of your current jobs to wait for (space to select, then enter to confirm)",
            choices= ID_alternatives
        ))

    questions.append(appform.Text(
        "other_dependencies",
        message="Other dependencies, if any (job IDs, separated by colon)"
    ))

    questions.append(appform.Integer(
        "simsteps",
        message="Set amount of steps"
    ))
    return questions

def Mesh(data):
    questions=[]
    questions.append(appform.Integer(
        "memory",
        message="Needed memory [GB]",
        default=210
    ))
    return questions

def Parallel(data):
    questions=[]
    return questions

def PostMeshNode(data):
    questions=[]
    questions.append(appform.Integer(
        "memory",
        message="Needed memory [GB]",
        default=210
    ))
    questions.append(appform.Confirm("sharenode", message="Allow sharing nodes with your other postprocessing jobs?", default=False))
    return questions

def PostComputeNode(data):
    questions=[]
    return questions

def Cosim(data):
    questions=[]
    return questions

def PostVTM(data):
    questions=[]
    questions.append(appform.Integer(
        "memory",
        message="Needed memory [GB]",
        default=210
    ))
    return questions

def wrapup(data):
    questions = []
    questions.append(appform.Confirm(
        "stageup",
        message="Stage files in scratch?",
        default=False
    ))

    questions.append(appform.Confirm(
        "submitnow",
        message="Submit job now?",
        default=False
    ))

    return questions
