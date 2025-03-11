#!/usr/bin/env python3
import subprocess
import csv
import json
import re
import time
from pathlib import Path
import tempfile
import os

# TODO FIXME use evaluation_config.json
valid_dirs = [
    "./evaluation_pipelines/valid",
    "./full_benchmark/intercode/pipelines",
    "./full_benchmark/pash_benchmark/benchmarks/unix50/scripts",
]
invalid_dirs = [
    "./evaluation_pipelines/invalid",
    "./full_benchmark/curated_mutants",
    "./full_benchmark/llm_injection/pipelines",
]
ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')

def is_meaningful_line(line):
    if line.strip() == "":
        return False
    if line.strip().startswith("#"):
        return False
    return True

def check_shellcheck(file_path):
    try:
        content = Path(file_path).read_text()
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".sh") as tmp:
            tmp.write("#!/bin/bash\n")
            tmp.write(content)
            tmp.flush()
            tmp_name = tmp.name
        result = subprocess.run(["shellcheck", tmp_name], capture_output=True, text=True, timeout=20)
        output = result.stdout + result.stderr
        print(output)
        os.remove(tmp_name)
        codes = re.findall(r'https://www\.shellcheck\.net/wiki/(\S+)', output)
        return ("OK" if result.returncode == 0 else "ERROR", output, codes)
    except Exception as e:
        return ("ERROR", str(e), [])

def check_ltsh(file_path):
    try:
        content = Path(file_path).read_text()
        lines = content.split("\n")
        lines = [l for l in lines if is_meaningful_line(l)]
        raw_output = ""
        for line in lines:
            result = subprocess.run(["ltsh"], input=line, capture_output=True, text=True, timeout=20)
            raw_output += result.stdout + result.stderr
        clean_output = ansi_escape.sub("", raw_output)
        output = clean_output
        print(output)
        return ("ERROR" if "typecheck error" in clean_output else "OK", output)
    except Exception as e:
        return ("ERROR", str(e))

def main():
    csv_file = "results.csv"
    json_file = "results.json"
    warnings_json_file = "shellcheck_warnings.json"
    all_results = []
    batch_results = []
    all_shellcheck_codes = set()
    csv_header = ["pipeline_file", "is buggy?", "shell check warning?", "ltsh warning?", "shell check processing time", "ltsh processing time", "shell check links"]
    with open(csv_file, "w", newline="") as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(csv_header)
    file_counter = 0
    for directory, buggy in [(d, True) for d in invalid_dirs] + [(d, False) for d in valid_dirs]:
        dir_path = Path(directory)
        if dir_path.exists() and dir_path.is_dir():
            for file in dir_path.rglob("*.sh"):
                if file.is_file():
                    start_shell = time.time()
                    sc_status, sc_output, sc_codes = check_shellcheck(str(file))
                    shell_processing_time = time.time() - start_shell
                    all_shellcheck_codes.update(sc_codes)
                    start_ltsh = time.time()
                    lt_status, lt_output = check_ltsh(str(file))
                    ltsh_processing_time = time.time() - start_ltsh
                    shell_warning = (sc_status == "ERROR")
                    if sc_codes:
                        warning_codes = set(sc_codes)
                        if warning_codes == {"SC2154"}:
                            shell_warning = False
                    record = {
                        "pipeline_file": str(file),
                        "is buggy?": buggy,
                        "shell check warning?": shell_warning,
                        "ltsh warning?": (lt_status == "ERROR"),
                        "shell check processing time": shell_processing_time,
                        "ltsh processing time": ltsh_processing_time,
                        "shell_check_output": sc_output,
                        "ltsh_output": lt_output,
                        "shell_check_links": sc_codes
                    }
                    batch_results.append(record)
                    file_counter += 1
                    if file_counter % 5 == 0:
                        with open(csv_file, "a", newline="") as f_csv:
                            writer = csv.writer(f_csv)
                            for r in batch_results:
                                writer.writerow([
                                    r["pipeline_file"],
                                    str(r["is buggy?"]).lower(),
                                    str(r["shell check warning?"]).lower(),
                                    str(r["ltsh warning?"]).lower(),
                                    f"{r['shell check processing time']:.3f}",
                                    f"{r['ltsh processing time']:.3f}",
                                    ";".join(r["shell_check_links"])
                                ])
                        all_results.extend(batch_results)
                        with open(json_file, "w") as f_json:
                            json.dump(all_results, f_json, indent=2)
                        batch_results = []
    if batch_results:
        with open(csv_file, "a", newline="") as f_csv:
            writer = csv.writer(f_csv)
            for r in batch_results:
                writer.writerow([
                    r["pipeline_file"],
                    str(r["is buggy?"]).lower(),
                    str(r["shell check warning?"]).lower(),
                    str(r["ltsh warning?"]).lower(),
                    f"{r['shell check processing time']:.3f}",
                    f"{r['ltsh processing time']:.3f}",
                    ";".join(r["shell_check_links"])
                ])
        all_results.extend(batch_results)
        with open(json_file, "w") as f_json:
            json.dump(all_results, f_json, indent=2)
    warnings_list = [{"code": code, "url": f"https://www.shellcheck.net/wiki/{code}", "isInteresting?": True} for code in sorted(all_shellcheck_codes)]
    with open(warnings_json_file, "w") as f_warn:
        json.dump(warnings_list, f_warn, indent=2)
    print(f"Results saved to {csv_file}, {json_file} and {warnings_json_file}")

if __name__ == "__main__":
    main()
