from typing import List
import os
import json

# Calculate line count
def line_count(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
        data = data.decode('utf-8', 'replace')
    lines = data.split("\n")
    counter = 0
    for line in lines:
        if line.strip() != "" and line.strip() != "#":
            counter += 1
    return counter

class Task:
    fullpath: str
    logfile: str
    line_count: int

    def __init__(self, filepath: str, logfile: str, line_count: int):
        self.fullpath = filepath
        self.logfile = logfile
        self.line_count = line_count

# Get tests from github folder
def get_github_scripts() -> List[Task]:
    root_path = os.path.abspath("tests/ShellExtractResults")
    projects = os.listdir(root_path)
    print(f"Collecting {len(projects)} projects from github")
    tasks = []
    # iterate on every project in the directory
    for project in projects:
        metadata_path = os.path.join(root_path, project, "metadata.json")
        if not os.path.exists(metadata_path):
            print("Incomplete project (ignoring):", project)
            continue
        with open(metadata_path, "r") as f: # read the metadata for the project
            metadata = json.load(f)
        for cfg in metadata:
            # Make the filepath
            filepath = os.path.join(root_path, cfg["identifier"]) + ".sh"
            logfile = os.path.join("suite", cfg["identifier"] + ".log")

            # guard b/c sometimes we couldn't copy the file; if it was a symbolic link
            # also guard for non-posix compliant scripts
            if os.path.exists(filepath) and cfg["posix_compliant"]:
                tasks.append(Task(filepath, logfile, cfg["line_count"]))
            else:
                continue

            # Ensure directory exists
            try:
                os.makedirs(os.path.dirname(logfile), exist_ok=True)
            except Exception as e:
                print(e)
                exit(0)
    print(f"Running {len(tasks)} scripts from github")
    return tasks

# Get tests from llm folder
def get_llm_scripts() -> List[Task]:
    root_path = os.path.abspath("tests/llm_scripts")
    scripts = os.listdir(root_path)
    print(f"Collecting {len(scripts)} scripts from the llm")
    tasks = []
    # iterate on every project in the directory
    for script in scripts:
        # Make the filepath
        filepath = os.path.join(root_path, script)
        logfile = os.path.join("suite/llm/", script.split(".sh")[0] + ".log")

        # guard for non-existend file
        if os.path.exists(filepath):
            tasks.append(Task(filepath, logfile, line_count(filepath)))
        else:
            print(f"{filepath} doesn't exist")
            continue

        # Ensure directory exists
        try:
            os.makedirs(os.path.dirname(logfile), exist_ok=True)
        except Exception as e:
            print(e)
            exit(0)
    return tasks

# Get tests from the user-study
def get_user_scripts() -> List[Task]:
    root_path = os.path.abspath("tests/user_study/research")
    scripts = os.listdir(root_path)
    print(f"Collecting {len(scripts)} scripts from the llm")
    tasks = []
    # iterate on every project in the directory
    for script in scripts:
        # Make the filepath
        filepath = os.path.join(root_path, script)
        logfile = os.path.join("suite/user_study/", script + ".log")

        # guard for non-existend file
        if os.path.exists(filepath):
            tasks.append(Task(filepath, logfile, line_count(filepath)))
        else:
            print(f"{filepath} doesn't exist")
            continue

        # Ensure directory exists
        try:
            os.makedirs(os.path.dirname(logfile), exist_ok=True)
        except Exception as e:
            print(e)
            exit(0)
    return tasks

# Get tests from debian repo (only works on omega)
def get_debian_scripts() -> List[Task]:
    if not os.path.exists("/home/ethan/Shared/DebianScripts"):
        print("WARNING -> cannot find debian scripts")
        return []
    root_path = "/home/ethan/Shared/DebianScripts"
    scripts = os.listdir(root_path)
    print(f"Collecting {len(scripts)} scripts from debian")
    tasks = []
    # iterate on every project in the directory
    for script in scripts:
        # Make the filepath
        filepath = os.path.join(root_path, script)
        logfile = os.path.join("suite/debian/", script.split(".sh")[0] + ".log")

        # guard for non-existent file
        if os.path.exists(filepath):
            tasks.append(Task(filepath, logfile, line_count(filepath)))
        else:
            print(f"{filepath} doesn't exist")
            continue

        # Ensure directory exists
        try:
            os.makedirs(os.path.dirname(logfile), exist_ok=True)
        except Exception as e:
            print(e)
            exit(0)
    return tasks
