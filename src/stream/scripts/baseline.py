#!/usr/bin/env python3
import subprocess
import csv
import json
import re
import time
from pathlib import Path
import tempfile
import os
import logging
from stream.config import CONFIG
from stream.shell_parser_util import extract_pipe_nodes_from_file

ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')

def is_meaningful_line(line):
    if line.strip() == "":
        return False
    if line.strip().startswith("#"):
        return False
    return True

def check_shellcheck(content):
    try:
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

def check_ltsh(content):
    try:
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
        print(f"Exception while trying to run ltsh: {e}")
        return ("ERROR", str(e))

def should_extract_all_pipelines(file_path):
    """Check if the first two lines contain '# stream disable' to determine extraction mode."""
    try:
        with open(file_path, 'r') as f:
            first_lines = [f.readline().strip() for _ in range(2)]
        
        for line in first_lines:
            if line.startswith('#') and 'stream disable' in line.lower():
                return False
        return True
    except Exception as e:
        print(f"Error reading file to check for 'stream disable': {e}")
        return True

def read_existing_records(csv_file):
    """Read existing records from CSV file to avoid rechecking."""
    existing_records = {}
    if os.path.exists(csv_file):
        try:
            with open(csv_file, "r", newline="") as f_csv:
                reader = csv.DictReader(f_csv)
                for row in reader:
                    # Use pipeline_file and pipeline as composite key
                    key = (row["pipeline_file"], row["pipeline"])
                    existing_records[key] = row
        except Exception as e:
            print(f"Error reading existing records: {e}")
    return existing_records

def normalize_path(path):
    """Normalize path to handle ./ prefixes and make sure paths are comparable."""
    # Remove ./ prefix if present
    if path.startswith('./'):
        path = path[2:]
    # Ensure consistent path separators
    return os.path.normpath(path)

def is_path_in_not_check_all_dirs(file_dir, not_check_all_dirs):
    """Check if a file directory is in the not_check_all_dirs list, handling path normalization."""
    normalized_file_dir = normalize_path(file_dir)
    
    for no_check_dir in not_check_all_dirs:
        normalized_no_check_dir = normalize_path(no_check_dir)
        
        # Direct match
        if normalized_file_dir == normalized_no_check_dir:
            return True
        
        # Check if file_dir is a subdirectory of no_check_dir
        if normalized_file_dir.startswith(normalized_no_check_dir + os.sep):
            return True
    
    return False

def process_parsing_failures(json_file, csv_file):
    """Process parsing failure logs and check them with ltsh and shellcheck."""
    parsing_error_log_path = CONFIG.get("parsing_error_log_path")
    if not parsing_error_log_path or not os.path.exists(parsing_error_log_path):
        print(f"Parsing error log not found at {parsing_error_log_path}")
        return
    
    print(f"Reading parsing errors from {parsing_error_log_path}")
    
    # Read the entire log file
    with open(parsing_error_log_path, 'r') as f:
        log_content = f.read()
    
    # Extract all "File contents:" sections
    file_contents_sections = []
    file_paths = []
    
    content_pattern = re.compile(r'Error parsing file: (.+?)\n.*?File contents:\n(.*?)(?=\n\[|\Z)', re.DOTALL)
    matches = content_pattern.finditer(log_content)
    
    # Process all matches to find unique content
    seen_contents = set()
    unique_contents = []
    unique_paths = []
    
    for match in matches:
        file_path = match.group(1).strip()
        content = match.group(2).strip()
        
        # Skip if we've seen this content before
        if content in seen_contents:
            continue
        
        seen_contents.add(content)
        unique_contents.append(content)
        unique_paths.append(file_path)
    
    print(f"Found {len(unique_contents)} unique file contents in parsing errors")
    
    # Load existing records from JSON file
    all_results = []
    if os.path.exists(json_file):
        with open(json_file, "r") as f_json:
            all_results = json.load(f_json)
    
    # Create a counter for unknown files
    unknown_counter = 1
    
    # Process each unique content
    new_results = []
    
    for i, (content, file_path) in enumerate(zip(unique_contents, unique_paths)):
        print(f"Processing content {i+1}/{len(unique_contents)} from {file_path}")
        
        # Determine the path to use in results
        result_path = file_path
        if file_path.startswith('/tmp') or file_path.startswith('tmp'):
            result_path = f"full_benchmark/pash_benchmark/unknown_file" + str(unknown_counter)
            unknown_counter += 1
        
        # 1. Check with shellcheck (write to temp file with shebang)
        start_shell = time.time()
        sc_status, sc_output, sc_codes = check_shellcheck(content)
        
        shell_processing_time = time.time() - start_shell
        
        # 2. Check with ltsh (pass content directly)
        start_ltsh = time.time()
        lt_status, lt_output = check_ltsh(content)
        ltsh_processing_time = time.time() - start_ltsh
        
        # Determine if there's a warning (exclude ignored codes)
        shell_warning = (sc_status == "ERROR")
        if sc_codes and all(code in ignored_sc_codes for code in sc_codes):
            print(f"Skipping warning for {result_path} because all codes are ignored")
            shell_warning = False
        
        # Record the results
        record = {
            "pipeline_file": result_path,
            "pipeline": content,
            "pipeline_index": i + 1,
            "is buggy?": False,
            "shell check warning?": shell_warning,
            "ltsh warning?": (lt_status == "ERROR"),
            "shell check processing time": shell_processing_time,
            "ltsh processing time": ltsh_processing_time,
            "shell_check_output": sc_output,
            "ltsh_output": lt_output,
            "shell_check_links": sc_codes
        }
        
        new_results.append(record)
        
        # Write to CSV (append mode)
        with open(csv_file, "a", newline="") as f_csv:
            writer = csv.writer(f_csv)
            writer.writerow([
                record["pipeline_file"],
                record["pipeline"],
                str(record["is buggy?"]).lower(),
                str(record["shell check warning?"]).lower(),
                str(record["ltsh warning?"]).lower(),
                f"{record['shell check processing time']:.3f}",
                f"{record['ltsh processing time']:.3f}",
                ";".join(record["shell_check_links"])
            ])
    
    # Update the JSON file with new results
    if new_results:
        all_results.extend(new_results)
        with open(json_file, "w") as f_json:
            json.dump(all_results, f_json, indent=2)
        print(f"Added {len(new_results)} parsing failure checks to results")

ignored_sc_codes = "SC2148,SC2012,SC2046,SC2086,SC2018,SC2019,SC2002,SC2006,SC2009,SC2035,SC2060,SC2061,SC2062,SC2063,SC2126,SC2154,SC2185,SC2196,SC2225".split(",")
def main():
    csv_file = "evaluation_results/baseline.csv"
    json_file = "evaluation_results/baseline.json"
    warnings_json_file = "evaluation_results/shellcheck_warnings.json"
    valid_dirs = CONFIG.get("valid_dirs")
    invalid_dirs = CONFIG.get("invalid_dirs")
    not_check_all_dirs = CONFIG.get("not_check_all_dirs", [])
    
    # # Clear the parsing error log file before starting
    # parsing_error_log_path = CONFIG.get("parsing_error_log_path")
    # if parsing_error_log_path:
    #     # Create the directory if it doesn't exist
    #     os.makedirs(os.path.dirname(parsing_error_log_path), exist_ok=True)
    #     # Clear or create the log file
    #     with open(parsing_error_log_path, 'w') as f:
    #         f.write("")
    #     print(f"Cleared parsing error log at {parsing_error_log_path}")
    
    # Read existing records to avoid rechecking
    existing_records = read_existing_records(csv_file)
    print(f"Found {len(existing_records)} existing records to skip rechecking")
    
    # Initialize files if they don't exist
    if not os.path.exists(csv_file):
        csv_header = ["pipeline_file", "pipeline", "is buggy?", "shell check warning?", "ltsh warning?", "shell check processing time", "ltsh processing time", "shell check links"]
        with open(csv_file, "w", newline="") as f_csv:
            writer = csv.writer(f_csv)
            writer.writerow(csv_header)
    
    all_results = []
    if os.path.exists(json_file):
        with open(json_file, "r") as f_json:
            all_results = json.load(f_json)
            print(f"Loaded {len(all_results)} existing results from JSON")
    
    batch_results = []
    all_shellcheck_codes = set()
    file_counter = 0
    
    for directory, buggy in [(d, True) for d in invalid_dirs] + [(d, False) for d in valid_dirs]:
        dir_path = Path(directory)
        if dir_path.exists() and dir_path.is_dir():
            # Process .sh, .bash, and .zsh files
            for file_ext in ["*.sh", "*.bash", "*.zsh"]:
                for file in dir_path.rglob(file_ext):
                    if file.is_file():
                        # Determine whether to extract all pipelines based on directory and file content
                        file_dir = str(file.parent)
                        extract_all_pipelines = True
                        
                        # Check if directory is in not_check_all_dirs
                        if is_path_in_not_check_all_dirs(file_dir, not_check_all_dirs):
                            extract_all_pipelines = False
                        
                        # Check if the file has "# stream disable" in first two lines
                        if should_extract_all_pipelines(file):
                            if not is_path_in_not_check_all_dirs(file_dir, not_check_all_dirs):  # Only override if not already set by directory
                                extract_all_pipelines = True
                        else:
                            extract_all_pipelines = False
                        
                        # Extract pipeline nodes from the file
                        print(f"Processing file: {file} (extract_all_pipelines={extract_all_pipelines})")
                        pipeline_nodes = extract_pipe_nodes_from_file(str(file), extract_all_pipelines)
                        
                        if not pipeline_nodes:
                            print(f"No pipelines found in {file}")
                            continue
                        
                        # Handle different return types based on extract_all_pipelines
                        if extract_all_pipelines:
                            # pipeline_nodes is list[PipeNode]
                            nodes_to_process = [(node, None) for node in pipeline_nodes]
                        else:
                            # pipeline_nodes is list[tuple[PipeNode, int]]
                            nodes_to_process = pipeline_nodes
                        
                        for idx, item in enumerate(nodes_to_process):
                            if extract_all_pipelines:
                                pipeline_node, _ = item
                            else:
                                pipeline_node, _ = item  # The second element is the line number, which we don't need here
                            
                            # Convert pipeline node to raw string
                            pipeline_str = pipeline_node.pretty()
                            # Ensure consistent backslash handling - replicating shell_parser behavior
                            pipeline_str = pipeline_str.replace("\\\\", "\\")
                            
                            # Check if this pipeline was already processed
                            key = (str(file), pipeline_str)
                            if key in existing_records:
                                print(f"Skipping already processed pipeline {idx+1}/{len(pipeline_nodes)} in {file}")
                                continue
                            
                            print(f"Checking pipeline {idx+1}/{len(pipeline_nodes)} in {file}:")
                            print(f"Pipeline: {pipeline_str}")
                            
                            start_shell = time.time()
                            sc_status, sc_output, sc_codes = check_shellcheck(pipeline_str)
                            shell_processing_time = time.time() - start_shell
                            all_shellcheck_codes.update(sc_codes)
                            
                            start_ltsh = time.time()
                            lt_status, lt_output = check_ltsh(pipeline_str)
                            ltsh_processing_time = time.time() - start_ltsh
                            
                            shell_warning = (sc_status == "ERROR")
                            if sc_codes:
                                warning_codes = set(sc_codes)
                                print(f"Warning codes: {warning_codes}")
                                if all(code in ignored_sc_codes for code in warning_codes):
                                    print(f"Skipping warning for pipeline {idx+1} in {file} because of the following codes: {warning_codes}")
                                    shell_warning = False
                            
                            record = {
                                "pipeline_file": str(file),
                                "pipeline": pipeline_str,
                                "pipeline_index": idx + 1,
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
                            
                        if file_counter % 5 == 0 and batch_results:
                            with open(csv_file, "a", newline="") as f_csv:
                                writer = csv.writer(f_csv)
                                for r in batch_results:
                                    writer.writerow([
                                        r["pipeline_file"],
                                        r["pipeline"],
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
                    r["pipeline"],
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
    
    # Process parsing failures
    process_parsing_failures(json_file, csv_file)
    
    # Save shell warning codes
    warnings_list = [{"code": code, "url": f"https://www.shellcheck.net/wiki/{code}", "isInteresting?": True} for code in sorted(all_shellcheck_codes)]
    with open(warnings_json_file, "w") as f_warn:
        json.dump(warnings_list, f_warn, indent=2)
    print(f"Results saved to {csv_file}, {json_file} and {warnings_json_file}")

if __name__ == "__main__":
    main()
