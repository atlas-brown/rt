#!/usr/bin/env python3
import subprocess
import csv
import json
import re
import time
import argparse
import contextlib
import sys
import traceback
from pathlib import Path
import tempfile
import os
import logging
from typing import TextIO
from stream.config import CONFIG
from stream.parser.shell_parser_util import extract_pipe_nodes_from_file
from tqdm import tqdm

ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
REPO_ROOT = Path(__file__).resolve().parents[3]

BENCHMARK_PROGRAM_TOTALS = {
    "GitHub": 114,
    "StackOverflow": 11,
    "LadderTypes": 12,
    "Koala": 481,
    "Intercode ALPHA": 205,
    "LLM": 120,
    "Handwritten": 11,
}
BENCHMARK_PROGRAM_ORDER = {category: index for index, category in enumerate(BENCHMARK_PROGRAM_TOTALS)}
BENCHMARK_CATEGORY_ALIASES = {
    "Ladder": "LadderTypes",
    "PaSh": "Koala",
    "Intercode": "Intercode ALPHA",
}


class CategoryProgress:
    def __init__(self, label: str, totals: dict[str, int], stream: TextIO, unit: str = "file"):
        self.label = label
        self.totals = totals
        self.stream = stream
        self.unit = unit
        self.done = {category: 0 for category in totals}
        self.current_category: str | None = None
        self.bar = None

    def advance(self, category: str) -> None:
        if category not in self.done:
            self.done[category] = 0
            self.totals[category] = 1

        if self.current_category != category:
            self._close_bar()
            self.current_category = category
            total = max(self.totals.get(category, 0), 1)
            self.bar = tqdm(
                total=total,
                initial=min(self.done.get(category, 0), total),
                desc=f"{self.label} on {category}",
                unit=self.unit,
                file=self.stream,
                dynamic_ncols=True,
                ascii=True,
                leave=True,
            )

        total = max(self.totals.get(category, 0), 1)
        if self.done[category] >= total:
            return
        self.done[category] += 1
        if self.bar is not None:
            self.bar.update(1)

    def finish(self) -> None:
        self._close_bar()

    def _close_bar(self) -> None:
        if self.bar is not None:
            if self.current_category is not None:
                total = max(self.totals.get(self.current_category, 0), 1)
                remaining = total - min(self.done.get(self.current_category, 0), total)
                if remaining > 0:
                    self.bar.update(remaining)
                    self.done[self.current_category] = total
            self.bar.close()
            self.bar = None


@contextlib.contextmanager
def redirect_process_output_to_log(log_file: str):
    os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
    log_handle = open(log_file, "a", encoding="utf-8", buffering=1)
    saved_stdout_fd = os.dup(1)
    saved_stderr_fd = os.dup(2)
    progress_stream = os.fdopen(os.dup(saved_stdout_fd), "w", buffering=1)
    try:
        os.dup2(log_handle.fileno(), 1)
        os.dup2(log_handle.fileno(), 2)
        with contextlib.redirect_stdout(log_handle), contextlib.redirect_stderr(log_handle):
            yield progress_stream
    finally:
        progress_stream.flush()
        os.dup2(saved_stdout_fd, 1)
        os.dup2(saved_stderr_fd, 2)
        os.close(saved_stdout_fd)
        os.close(saved_stderr_fd)
        progress_stream.close()
        log_handle.close()


def get_shellcheck_command():
    return CONFIG.get("shellcheck_command", "shellcheck")


def get_ltsh_command():
    return CONFIG.get("ltsh_command", "ltsh")


def get_ltsh_typedb_path():
    typedb_path = Path(CONFIG.get("ltsh_typedb_path", "ltsh_config/typedb"))
    if not typedb_path.is_absolute():
        typedb_path = REPO_ROOT / typedb_path
    return typedb_path

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
        result = subprocess.run([get_shellcheck_command(), tmp_name], capture_output=True, text=True, timeout=20)
        output = result.stdout + result.stderr
        print(output)
        os.remove(tmp_name)
        codes = re.findall(r'https://www\.shellcheck\.net/wiki/(\S+)', output)
        return ("OK" if result.returncode == 0 else "ERROR", output, codes)
    except Exception as e:
        return ("ERROR", str(e), [])

def check_ltsh(content):
    try:
        typedb_path = get_ltsh_typedb_path()
        if not typedb_path.exists():
            raise FileNotFoundError(f"ltsh typedb not found at {typedb_path}")

        lines = content.split("\n")
        lines = [l for l in lines if is_meaningful_line(l)]
        raw_output = ""
        env = os.environ.copy()
        env["TYPEDB"] = str(typedb_path)
        for line in lines:
            result = subprocess.run(
                [get_ltsh_command()],
                input=line,
                capture_output=True,
                text=True,
                timeout=20,
                env=env,
            )
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
                    key = (normalize_path(row["pipeline_file"]), row["pipeline"])
                    existing_records[key] = row
        except Exception as e:
            print(f"Error reading existing records: {e}")
    return existing_records


def read_existing_results(json_file):
    """Read existing JSON results keyed by normalized pipeline identity."""
    existing_results = {}
    if os.path.exists(json_file):
        try:
            with open(json_file, "r") as f_json:
                for record in json.load(f_json):
                    key = (normalize_path(record["pipeline_file"]), record["pipeline"])
                    existing_results[key] = record
        except Exception as e:
            print(f"Error reading existing JSON results: {e}")
    return existing_results


def write_results(csv_file, json_file, results_by_key):
    """Rewrite CSV/JSON outputs from the canonical keyed result map."""
    csv_header = [
        "pipeline_file",
        "pipeline",
        "is buggy?",
        "shell check warning?",
        "ltsh warning?",
        "shell check processing time",
        "ltsh processing time",
        "shell check links",
    ]
    ordered_records = sorted(
        results_by_key.values(),
        key=lambda r: (normalize_path(r["pipeline_file"]), r["pipeline"]),
    )

    with open(csv_file, "w", newline="") as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(csv_header)
        for record in ordered_records:
            writer.writerow([
                record["pipeline_file"],
                record["pipeline"],
                str(record["is buggy?"]).lower(),
                str(record["shell check warning?"]).lower(),
                str(record["ltsh warning?"]).lower(),
                f"{record['shell check processing time']:.3f}",
                f"{record['ltsh processing time']:.3f}",
                ";".join(record["shell_check_links"]),
            ])

    with open(json_file, "w") as f_json:
        json.dump(ordered_records, f_json, indent=2)

def normalize_path(path):
    """Normalize path to handle ./ prefixes and make sure paths are comparable."""
    # Remove ./ prefix if present
    if path.startswith('./'):
        path = path[2:]
    # Ensure consistent path separators
    return os.path.normpath(path)

def infer_benchmark_name(path):
    normalized_path = normalize_path(str(path)).replace(os.sep, "/")
    benchmark_patterns = CONFIG.get("benchmark names", {})
    for pattern, name in benchmark_patterns.items():
        if re.match(pattern, normalized_path):
            return BENCHMARK_CATEGORY_ALIASES.get(str(name), str(name))

    parts = Path(normalized_path).parts
    if "full_benchmark" in parts:
        index = parts.index("full_benchmark")
        if index + 1 < len(parts):
            return BENCHMARK_CATEGORY_ALIASES.get(parts[index + 1], parts[index + 1])
    if "evaluation_pipelines" in parts:
        return "Handwritten"
    return parts[0] if parts else "unknown"

def collect_script_files(directories, buggy):
    script_files = []
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            continue
        for file_ext in ["*.sh", "*.bash", "*.zsh"]:
            for file in dir_path.rglob(file_ext):
                if file.is_file():
                    script_files.append((file, buggy))
    return script_files

def count_files_by_category(script_files):
    counts = {}
    for file, _ in script_files:
        category = infer_benchmark_name(file)
        counts[category] = counts.get(category, 0) + 1
    return counts

def collect_pipeline_work_items(script_files, not_check_all_dirs):
    work_items = []
    for file, buggy in sorted(
        script_files,
        key=lambda item: (
            BENCHMARK_PROGRAM_ORDER.get(infer_benchmark_name(item[0]), len(BENCHMARK_PROGRAM_ORDER)),
            normalize_path(str(item[0])),
        ),
    ):
        file_dir = str(file.parent)
        extract_all_pipelines = True

        if is_path_in_not_check_all_dirs(file_dir, not_check_all_dirs):
            extract_all_pipelines = False

        if should_extract_all_pipelines(file):
            if not is_path_in_not_check_all_dirs(file_dir, not_check_all_dirs):
                extract_all_pipelines = True
        else:
            extract_all_pipelines = False

        print(f"Processing file: {file} (extract_all_pipelines={extract_all_pipelines})")
        pipeline_nodes = extract_pipe_nodes_from_file(str(file), extract_all_pipelines)

        if not pipeline_nodes:
            print(f"No pipelines found in {file}")
            continue

        if extract_all_pipelines:
            nodes_to_process = [(node, None) for node in pipeline_nodes]
        else:
            nodes_to_process = pipeline_nodes

        category = infer_benchmark_name(file)
        for idx, item in enumerate(nodes_to_process):
            pipeline_node, _ = item
            pipeline_str = pipeline_node.pretty()
            pipeline_str = pipeline_str.replace("\\\\", "\\")
            work_items.append({
                "file": file,
                "buggy": buggy,
                "category": category,
                "pipeline_index": idx + 1,
                "pipeline_count": len(nodes_to_process),
                "pipeline": pipeline_str,
            })

    return work_items

def count_unique_work_items_by_category(work_items):
    unique_by_category = {}
    for item in work_items:
        key = (normalize_path(str(item["file"])), item["pipeline"])
        unique_by_category.setdefault(item["category"], set()).add(key)
    return {category: len(pipelines) for category, pipelines in unique_by_category.items() if pipelines}

def benchmark_program_totals_for(work_items):
    categories = {item["category"] for item in work_items}
    return {
        category: BENCHMARK_PROGRAM_TOTALS[category]
        for category in BENCHMARK_PROGRAM_TOTALS
        if category in categories
    }

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

def process_parsing_failures(results_by_key):
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
        result_key = (normalize_path(result_path), content)
        if result_key in results_by_key:
            print(f"Skipping already processed parsing failure for {result_path}")
            continue
        
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
    if new_results:
        for record in new_results:
            result_key = (normalize_path(record["pipeline_file"]), record["pipeline"])
            results_by_key[result_key] = record
        print(f"Added {len(new_results)} parsing failure checks to results")

ignored_sc_codes = "SC2148,SC2012,SC2046,SC2086,SC2018,SC2019,SC2002,SC2006,SC2009,SC2035,SC2060,SC2061,SC2062,SC2063,SC2126,SC2154,SC2185,SC2196,SC2225".split(",")
def main(progress_label=None, progress_stream=None):
    csv_file = "evaluation_results/baseline.csv"
    json_file = "evaluation_results/baseline.json"
    warnings_json_file = "evaluation_results/shellcheck_warnings.json"
    valid_dirs = CONFIG.get("valid_dirs")
    invalid_dirs = CONFIG.get("invalid_dirs")
    not_check_all_dirs = CONFIG.get("not_check_all_dirs", [])

    # Read existing records to avoid rechecking
    existing_records = read_existing_records(csv_file)
    print(f"Found {len(existing_records)} existing records to skip rechecking")
    results_by_key = read_existing_results(json_file)
    print(f"Loaded {len(results_by_key)} canonical results from JSON")

    all_shellcheck_codes = set()
    file_counter = 0

    script_files = []
    for directory, buggy in [(d, True) for d in invalid_dirs] + [(d, False) for d in valid_dirs]:
        script_files.extend(collect_script_files([directory], buggy))
    work_items = collect_pipeline_work_items(script_files, not_check_all_dirs)

    progress = None
    progress_seen = {}
    if progress_label and progress_stream is not None:
        progress = CategoryProgress(
            progress_label,
            benchmark_program_totals_for(work_items),
            progress_stream,
            unit="program",
        )

    for item in work_items:
        file = item["file"]
        pipeline_str = item["pipeline"]
        category = item["category"]

        # Check if this pipeline was already processed
        key = (normalize_path(str(file)), pipeline_str)
        if key in existing_records:
            print(f"Skipping already processed pipeline {item['pipeline_index']}/{item['pipeline_count']} in {file}")
            continue

        print(f"Checking pipeline {item['pipeline_index']}/{item['pipeline_count']} in {file}:")
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
                print(f"Skipping warning for pipeline {item['pipeline_index']} in {file} because of the following codes: {warning_codes}")
                shell_warning = False

        record = {
            "pipeline_file": str(file),
            "pipeline": pipeline_str,
            "pipeline_index": item["pipeline_index"],
            "is buggy?": item["buggy"],
            "shell check warning?": shell_warning,
            "ltsh warning?": (lt_status == "ERROR"),
            "shell check processing time": shell_processing_time,
            "ltsh processing time": ltsh_processing_time,
            "shell_check_output": sc_output,
            "ltsh_output": lt_output,
            "shell_check_links": sc_codes
        }
        results_by_key[key] = record
        file_counter += 1

        if file_counter % 5 == 0:
            write_results(csv_file, json_file, results_by_key)
        if progress is not None:
            seen = progress_seen.setdefault(category, set())
            progress_key = (normalize_path(str(file)), pipeline_str)
            if progress_key not in seen:
                seen.add(progress_key)
                progress.advance(category)

    if progress is not None:
        progress.finish()
    
    # Process parsing failures
    process_parsing_failures(results_by_key)
    write_results(csv_file, json_file, results_by_key)
    
    # Save shell warning codes
    warnings_list = [{"code": code, "url": f"https://www.shellcheck.net/wiki/{code}", "isInteresting?": True} for code in sorted(all_shellcheck_codes)]
    with open(warnings_json_file, "w") as f_warn:
        json.dump(warnings_list, f_warn, indent=2)
    print(f"Results saved to {csv_file}, {json_file} and {warnings_json_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ShellCheck and LadderTypes baselines.")
    parser.add_argument("--progress", action="store_true",
                        help="Show per-category progress on stdout.")
    parser.add_argument("--progress-label", default="ShellCheck/LadderTypes",
                        help="Label to display before each progress bar.")
    parser.add_argument("--log-file", default=None,
                        help="Write baseline logs and tool output to this file.")
    args = parser.parse_args()

    original_stdout = sys.stdout

    try:
        if args.progress and args.log_file:
            with redirect_process_output_to_log(args.log_file) as progress_stream:
                main(progress_label=args.progress_label, progress_stream=progress_stream)
        else:
            main(
                progress_label=args.progress_label if args.progress else None,
                progress_stream=original_stdout if args.progress else None,
            )
    except Exception:
        if args.log_file:
            with open(args.log_file, "a", encoding="utf-8") as log_handle:
                traceback.print_exc(file=log_handle)
            sys.exit(1)
        raise
