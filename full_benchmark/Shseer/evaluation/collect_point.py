import argparse
import json
import os
import subprocess
import sys
import time
from multiprocessing import Pool
from typing import List, Tuple

from reporter import Report, ShseerResult
from vformat import ClassEncoder, ErrorSummary, VersionBenchmark
from common import get_github_scripts, get_debian_scripts, get_llm_scripts, get_user_scripts, Task

class Completion:
    task: Task
    report: Report
    perf: float
    did_timeout: bool
    did_crash: bool
    reason_crash: str

    def __init__(self, task: Task, report: Report, perf: float, did_timeout: bool, did_crash: bool, reason_crash: str):
        self.task = task
        self.report = report
        self.perf = perf
        self.did_timeout = did_timeout
        self.did_crash = did_crash
        self.reason_crash = reason_crash

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

# Get tests from github folder
def get_github_scripts() -> List[Task]:
    root_path = os.path.abspath("tests/ShellExtractResults")
    projects = os.listdir(root_path)
    print(f"Collecting {len(projects)} projects from github")
    tasks = []
    # iterate on every project in the directory
    for project in projects:
        metadata_path = os.path.join(root_path, project, "metadata.json")
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

def __run__(input: Tuple[int, Task]) -> Completion:
    index, task = input
    # default vars
    cwd = "../shseer/python/shseer" 
    did_timeout = False
    did_crash = False
    reason_crash = ""
    report = Report(None)
    seconds_start = 0
    seconds_end = 0
    try:
        with open(task.logfile, "w+") as f:
            program = ["python3", "symb.py", task.fullpath]
            seconds_start = time.perf_counter()
            process = subprocess.run(program, timeout=30, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd)
            seconds_end = time.perf_counter()
            output = process.stdout + process.stderr
            try:
                report = Report(output.strip())
                print(f"{os.path.basename(task.fullpath)} (Script #{index})",flush=True)
            except json.JSONDecodeError as e:
                did_crash = True
                reason_crash = output
                print(f"{os.path.basename(task.fullpath)} got {output}")
            f.write(output)
    except subprocess.TimeoutExpired as e:
        print(f"{os.path.basename(task.fullpath)} Timed-Out")
        did_timeout = True
    except subprocess.CalledProcessError as e:
        print(f"Invalid Startup {os.path.basename(task.fullpath)} because {e}")
        reason_crash = e
        did_crash = True

    # Get time of process
    perf = seconds_end - seconds_start
    return Completion(task, report, perf, did_timeout, did_crash, str(reason_crash))

def test_parse() -> bool:
    cwd = "../shseer/python/shseer"
    root_path = os.path.abspath("tests/cases/correct.sh")
    program = ["python3", "symb.py", root_path]
    process = subprocess.run(program, timeout=20, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd)
    output = process.stdout + process.stderr
    try:
        report = Report(output.strip())
        print(report.__dict__)
        return True
    except json.JSONDecodeError as e:
        print(output)
        print(e)
        return False

def calc_benchmark(version: str, group: str, parallelize: bool, tasks: List[Task]) -> VersionBenchmark:
    MAX_SUBPROCESSES = 1
    if parallelize:
        MAX_SUBPROCESSES = 30 # use process parallelism
    pool = Pool(MAX_SUBPROCESSES)
    total_lines = 0 # count lines
    total_time_no_timeout = 0
    summary = ErrorSummary()

    # Map the tasks to completions
    indexed_tasks = []
    index = 1
    for task in tasks:
        indexed_tasks.append((index, task))
        index += 1
    res_output = pool.map(__run__, indexed_tasks)

    for output in res_output:
        task = output.task
        report = output.report
        perf = output.perf

        # Handle crash and timeout cases
        if output.did_crash:
            summary.add_crash(task.fullpath, output.reason_crash)
            continue
        if output.did_timeout:
            summary.add_timeout(task.fullpath)
            continue

        # Handle report's judgement
        match report.judgement:
            case ShseerResult.SymbOk:
                summary.add_good(task.fullpath)
            case ShseerResult.UNKNOWN:
                summary.add_unknown(task.fullpath)
            case ShseerResult.SymbError:
                summary.add_bad(task.fullpath)
            case ShseerResult.TIMEOUT:
                print(f"{os.path.basename(task.fullpath)} Timed-Out (inside executable)")
                summary.add_timeout(task.fullpath)
                continue
            case ShseerResult.ParseError:
                summary.add_parse(task.fullpath)
            case _:
                summary.add_panic(task.fullpath)

        # Compile performance results
        total_lines += task.line_count
        total_time_no_timeout += perf

        # Add strings
        summary.add_reason(report.error_messages, task.fullpath)
        summary.add_error_msg(report.unimplemented_messages)
        summary.add_form(report.expansion_forms)
        summary.add_time(report.time)

    with open(f"trial_results_{group}.json", "w") as f:
        json.dump(summary, f, cls=ClassEncoder, indent=" ")

    if total_lines != 0:
        avg_time = (total_time_no_timeout / total_lines) * 1000
    else:
        avg_time = 0
    return VersionBenchmark(
        version=version,
        scripts_good=summary.good,
        scripts_bad=summary.bad,
        scripts_panic=summary.panic,
        scripts_crash=summary.crash,
        scripts_timeout=summary.timeout,
        scripts_parse=summary.parse,
        scripts_unknown=summary.unknown,
        time_line=avg_time,
        time_script=total_time_no_timeout,
    )

GITHUB = "github"
LLM = "llm"
DEBIAN = "debian"
USERSTUDY = "user_study"

if __name__ == "__main__":
    groups = []
    no_perf = False
    commit_id = subprocess.check_output("git rev-parse HEAD", shell=True, text=True).strip()
    timestamp = time.asctime(time.localtime())
    parser = argparse.ArgumentParser(description='Collect evaluation')
    parser.add_argument('--github', action="store_true", help='Run Shseer against the github scripts')
    parser.add_argument('--llm', action="store_true", help='Run Shseer against the llm-generated scripts')
    parser.add_argument('--debian', action="store_true", help='Run Shseer against the debian scripts')
    parser.add_argument('--user_study', action="store_true", help='Run Shseer against the debian scripts')
    parser.add_argument('--all', action="store_true", help='Run Shseer against all scripts')
    parser.add_argument('--no_perf', action="store_true", help='Run Shseer in parallel and ignore performance tests')
    parser.add_argument('--commit_id', type=str, default=None, help='Override commit id')
    parser.add_argument('--filepath', type=str, default="./versions_overtime.json", help="Where to save the progress")
    parser.add_argument('--use_existing', action="store_true", help="Used by run_benchmark.sh. Ignored here")
 
    ARGS = parser.parse_args(sys.argv[1:])

    if ARGS.github:
        groups.append(GITHUB)
    if ARGS.llm:
        groups.append(LLM)
    if ARGS.debian:
        groups.append(DEBIAN)
    if ARGS.user_study:
        groups.append(USERSTUDY)
    if ARGS.no_perf:
        print("Parallelizing run")
        no_perf = True
    if ARGS.all:
        groups = [GITHUB, LLM, DEBIAN, USERSTUDY]
    groups = list(set(groups)) # remove duplicates

    if not os.getcwd().endswith("evaluation"):
        print("Run from within the evaluation directory")
        exit(1)

    if len(groups) == 0:
        print("No groups of scripts. Use --llm, --github, --debian, --user_study")
        exit(0)

    if not test_parse():
        print("Cannot parse output of Shseer. Tell Ethan to update eval to handle the update to Shseer")
        exit(0)

    # Set commit id
    if ARGS.commit_id is not None:
        commit_id = ARGS.commit_id

    # Read the old version 
    filepath = ARGS.filepath
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            data = f.read()
            if data == "":
                old_versions = {}
            else:
                old_versions = json.loads(data)
    else:
        old_versions = {}

    # Calculate the results
    for group in groups:
        print(f"Starting {group}")

        # Get the tests
        tests = []
        if group == GITHUB:
            tests = get_github_scripts()
        elif group == LLM:
            tests = get_llm_scripts()
        elif group == DEBIAN:
            tests = get_debian_scripts()
        elif group == USERSTUDY:
            tests = get_user_scripts()
        if len(tests) == 0:
            print(f"{group} has no tests")
            continue
        
        # Compute result
        version_benchmark = calc_benchmark(commit_id + "." + group, group, no_perf, tests)
        version_benchmark.included = [group]
        if no_perf:
            version_benchmark.included.append("no_perf [performance results might be inaccurate]")
        version_benchmark.timestamp = timestamp

        # Add result
        old_versions[version_benchmark.version] = version_benchmark

    # Write back with new versions appended
    print("Writing version results to file",flush=True)
    with open(filepath, "w") as f:
        json.dump(old_versions, f, cls=ClassEncoder, indent=" ")
