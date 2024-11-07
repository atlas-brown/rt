import json
from collections import defaultdict
from shseer.shellcheck_map import SC_MAP
import argparse
import subprocess
import sys
from pathlib import Path

def get_normfilename(filename):
    return str(Path(*Path(filename).parts[-2:]))

def get_shellcheck_results(benchmark_name : str):
    
    results = json.load(open("shellcheck_output.json"))
    
    benchmark_dct =  results[benchmark_name] # File -> Code -> Count 
    
    #Turn this into a Code -> File -> Count
    code_dct = defaultdict(list)
    for file in benchmark_dct.keys():
        for code in benchmark_dct[file].keys():
            if code not in SC_MAP:
                continue
            shseer_code = SC_MAP[code]().code
            #Get the repo/filename ignore the local filepath 
            filecomp = get_normfilename(file)
            code_dct[shseer_code].append(filecomp)
    return code_dct

def get_shseer_results_file(benchmark_name : str):
    if benchmark_name == "github":
        return "trial_results_github.json"
    else:
        raise ValueError(f"Unknown benchmark {benchmark_name}")

def get_shseer_results(benchmark_name : str):
    results = json.load(open(get_shseer_results_file(benchmark_name)))
    
    dct =  results["reasons_whom"] # Code -> Files 
    for code in dct.keys():
        dct[code] = [get_normfilename(file) for file in dct[code]]
    return dct 


def analysis(benchmark_name : str,commit_id : str,only_milestone : bool):
    shellcheck_results = get_shellcheck_results(benchmark_name)
    shseer_results = get_shseer_results(benchmark_name)
    all_codes_set = set(shellcheck_results.keys()).union(set(shseer_results.keys()))
    all_codes = { i : "" for i in all_codes_set}
    filename  = f"analysis_{benchmark_name}_{commit_id}"
    if only_milestone:
        all_codes = {}
        for code in MILESTONE_CODES:
            x=  SC_MAP[code]()
            all_codes[x.code] =  x.report
        filename += "_milestone"
    # For each code get:
    # Total number in Shellcheck
    # Total number in Shseer
    # Number of common files
    # Number in shellcheck but not in shseer
    # Number in shseer but not in shellcheck
    # Write this to a CSV file
    with open(f"{filename}.csv","w") as f:
        f.write("Code,Meaning,Total Shellcheck,Total Shseer,Common,Shellcheck Only,Shseer Only\n")
        for code in all_codes:
            shellcheck_files = set(shellcheck_results[code]) if code in shellcheck_results else set()
            shseer_files = set(shseer_results[code]) if code in shseer_results else set()
            common = shellcheck_files.intersection(shseer_files)
            shellcheck_only = shellcheck_files - common
            shseer_only = shseer_files - common
            f.write(f"{code},\"{all_codes[code]}\",{len(shellcheck_files)},{len(shseer_files)},{len(common)},{len(shellcheck_only)},{len(shseer_only)}\n")
    print("Done")
    
GITHUB = "github"
LLM = "llm"
DEBIAN = "debian"
USERSTUDY = "user_study"
MILESTONE_CODES = ['SC2030', 'SC2031', 'SC2034', 'SC2043', 'SC2050', 'SC2071', 'SC2072', 'SC2079', 
                   'SC2080', 'SC2114', 'SC2115', 'SC2119', 'SC2120', 'SC2123', 'SC2151', 'SC2152', 'SC2153', 'SC2154', 'SC2157', 
                   'SC2170', 'SC2193', 'SC2195', 'SC2213', 'SC2214', 'SC2220', 'SC2221', 'SC2222', 'SC2241', 'SC2242', 'SC2249', 
                   'SC2252', 'SC2269', 'SC2286', 'SC2309', 'SC2317', 'SC2130']
if __name__ == "__main__":
    commit_id = subprocess.check_output("git rev-parse HEAD", shell=True, text=True).strip()

    parser = argparse.ArgumentParser(description='Collect evaluation')
    parser.add_argument('--github', action="store_true", help='Run Shseer against the github scripts')
    # parser.add_argument('--llm', action="store_true", help='Run Shseer against the llm-generated scripts')
    # parser.add_argument('--debian', action="store_true", help='Run Shseer against the debian scripts')
    # parser.add_argument('--user_study', action="store_true", help='Run Shseer against the debian scripts')
    # parser.add_argument('--all', action="store_true", help='Run Shseer against all scripts')
    # parser.add_argument('--no_perf', action="store_true", help='Run Shseer in parallel and ignore performance tests')
    # parser.add_argument('--commit_id', type=str, default=None, help='Override commit id')
    # parser.add_argument('--filepath', type=str, default="./versions_overtime.json", help="Where to save the progress")
    # parser.add_argument('--use_existing', action="store_true", help="Used by run_benchmark.sh. Ignored here")
    parser.add_argument("--milestone", action="store_true", help="Only get milestone codes")
    ARGS: argparse.Namespace = parser.parse_args(sys.argv[1:])
    only_milestone = ARGS.milestone
    if ARGS.github:
        analysis(GITHUB,commit_id,only_milestone)