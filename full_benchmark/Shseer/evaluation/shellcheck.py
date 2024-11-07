import argparse
import json
import os
import subprocess
import sys
from multiprocessing import Pool
from typing import List, Tuple
import shutil
import re

def is_tool(name):
    return shutil.which(name) is not None

from common import get_github_scripts, get_debian_scripts, get_llm_scripts, get_user_scripts, Task

class Completion:
    task: Task
    codes: dict

    def __init__(self, task: Task, codes: dict):
        self.task = task
        self.codes = codes
        

def __run__(input: Tuple[int, Task]) -> Completion:
    _, task = input
    codes = {}
    try:
        with open(task.logfile, "w+") as f:
            program = ["shellcheck", "--color=never", task.fullpath]
            process = subprocess.run(program, timeout=5, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = process.stdout + process.stderr
            f.write(output)
            if "For more information:" in output:
                output = output.split("For more information:")[0]

            matches = re.findall(r"SC\d\d\d\d", output)
            for match in matches:
                if match in codes:
                    codes[match] += 1
                else:
                    codes[match] = 1
    except subprocess.TimeoutExpired as e:
        print(f"{os.path.basename(task.fullpath)} Timed-Out")
    except subprocess.CalledProcessError as e:
        print(f"Invalid Startup {os.path.basename(task.fullpath)} because {e}")

    return Completion(task, codes)

def calc_benchmark(group: str, tasks: List[Task]) -> dict:
    MAX_SUBPROCESSES = 8 # using 8 subprocess for speed :)
    pool = Pool(MAX_SUBPROCESSES)

    # Map the tasks to completions
    indexed_tasks = []
    index = 1
    for task in tasks:
        indexed_tasks.append((index, task))
        index += 1
    res_output = pool.map(__run__, indexed_tasks)

    summary = {}
    for output in res_output:
        task = output.task
        report = output.codes

        summary[task.fullpath] = report
    return summary

GITHUB = "github"
LLM = "llm"
DEBIAN = "debian"
USERSTUDY = "user_study"

if __name__ == "__main__":
    if not is_tool("shellcheck"):
        print("Shellcheck not found on the PATH")
        print("Please install it using the instructions from https://www.shellcheck.net/")
        exit(1)
    groups = []
    parser = argparse.ArgumentParser(description='Collect evaluation for Shellcheck')
    parser.add_argument('--github', action="store_true", help='Run Shellcheck against the github scripts')
    parser.add_argument('--llm', action="store_true", help='Run Shellcheck against the llm-generated scripts')
    parser.add_argument('--debian', action="store_true", help='Run Shellcheck against the debian scripts')
    parser.add_argument('--user_study', action="store_true", help='Run Shellcheck against the debian scripts')
    parser.add_argument('--all', action="store_true", help='Run Shellcheck against all scripts')
    parser.add_argument('--filepath', type=str, default="./shellcheck_output.json", help="Where to save the progress")
 
    ARGS = parser.parse_args(sys.argv[1:])
    if ARGS.github:
        groups.append(GITHUB)
    if ARGS.llm:
        groups.append(LLM)
    if ARGS.debian:
        groups.append(DEBIAN)
    if ARGS.user_study:
        groups.append(USERSTUDY)
    if ARGS.all:
        groups = [GITHUB, LLM, DEBIAN, USERSTUDY]
    groups = list(set(groups)) # remove duplicates

    if not os.getcwd().endswith("evaluation"):
        print("Run from within the evaluation directory")
        exit(1)

    if len(groups) == 0:
        print("No groups of scripts. Use --llm, --github, --debian, --user_study, or --all")
        exit(0)

    # Calculate the results
    output_result = {}
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
        output_result[group] = calc_benchmark(group, tests)

    # Write back with new versions appended
    print("Writing version results to file",flush=True)
    with open(ARGS.filepath, "w") as f:
        json.dump(output_result, f, indent=" ")