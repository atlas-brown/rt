import multiprocessing
import os
import json
import logging
import time
import re
from functools import partial
from typing import List, Tuple
import jpype
import jpype.imports
if not jpype.isJVMStarted():
    jpype.startJVM(classpath=["jars/automaton.jar"])
from stream.type_checker import TypeChecker
from stream.tool_error import PashAnnotationParsingError, TimeoutError
import argparse
from stream.config import CONFIG

# Default values now come from CONFIG
ENABLE_TIMEOUT = CONFIG.get("enable_timeout", False)
TIMEOUT_SECONDS = CONFIG.get("timeout_seconds", 10)

IS_BUGGY_LABEL = "is buggy?"
SIGNALED_LABEL = "warning signaled?"
PIPELINE_ID_LABEL = "id"
CATEGORY_LABEL = "category"
CRASH_REASON_LABEL = "tool runtime error"
TIMEOUT_REASON = f"Timeout after {TIMEOUT_SECONDS}s"

enable_user_annotation = CONFIG.get("enable_user_annotation", True)

# class LogHandler(logging.Handler):
#     def __init__(self):
#         super().__init__()
#         self.log_entries = []
#
#     def emit(self, record):
#         log_entry = self.format(record)
#         self.log_entries.append(log_entry)
#
# log_handler = LogHandler()
# logging.basicConfig(level=logging.INFO, handlers=[log_handler, logging.StreamHandler()])
# logger = logging.getLogger()

def find_scripts(directories: list[str]) -> list[str]:
    script_addresses = []
    
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.sh')) or file.endswith(('.bash')) or file.endswith(('.zsh')):
                    file_path = os.path.join(root, file)
                    script_addresses.append(file_path)
    
    return script_addresses


def calculate_accuracy(labels, preds):
    correct_count = sum(1 for label, pred in zip(labels, preds) if label == pred)
    denom = sum(1 for label in labels if label is not None)
    if denom == 0:
        return 0.0
    return correct_count / denom

def calculate_precision(labels, preds):
    TP = sum(1 for label, pred in zip(labels, preds) if label == pred and label)
    denom = sum(1 for pred in preds if pred)
    if denom == 0:
        return 0.0
    return TP / denom

def calculate_recall(labels, preds):
    denom = sum(1 for label in labels if label)
    if denom == 0:
        return 0.0
    recall = sum(1 for label, pred in zip(labels, preds) if label == pred and label) / denom
    return recall


def evaluate_pipeline_content(address: str, check_all_pipelines: bool) -> list[dict]:
    pipeline_data_template = {
        "address": address,
        "content": None,
        IS_BUGGY_LABEL: None,
        SIGNALED_LABEL: None,
        CRASH_REASON_LABEL: None,
        "pash annotations error": None,
        "error message generated": None,
        "evaluation_time": None,
        "tainted": None,
        # "notes": ""
    }
    pipeline_data_list = []
    
    try:        
        logging.info(f"Evaluating pipeline from {address}")
        type_checker = TypeChecker(
            address, 
            enable_user_annotations=enable_user_annotation, 
            enable_stage_timeout=ENABLE_TIMEOUT, 
            stage_timeout=TIMEOUT_SECONDS, 
            check_all_pipelines=check_all_pipelines,
            enable_rule_no_empty_output=CONFIG.get("enable_rule_no_empty_output", True),
            enable_rule_no_ignored_input=CONFIG.get("enable_rule_no_ignored_input", True),
            enable_rule_no_meaningless_command=CONFIG.get("enable_rule_no_meaningless_command", True),
            enable_rule_no_sort_non_numeric_with_numeric_input=CONFIG.get("enable_rule_no_sort_non_numeric_with_numeric_input", True)
        )

        try:
            while True:
                start_time = time.time()
                logging.debug(f'Evaluating pipeline from {address}')
                checking_result = type_checker.check_next()
                if checking_result is None:
                    break

                end_time = time.time()
                elapsed_time = end_time - start_time

                pipeline_data = pipeline_data_template.copy()
                pipeline_data[SIGNALED_LABEL] = checking_result.ill_typed
                pipeline_data["content"] = checking_result.pipeline_content
                pipeline_data["evaluation_time"] = f"{elapsed_time:.2f}s"
                pipeline_data["automata_size"] = type_checker.max_automata_size
                pipeline_data["tainted"] = checking_result.tainted
                if checking_result.ill_typed:
                    pipeline_data["error message generated"] = checking_result.message
                    logging.info(f'Error detected in pipeline {checking_result.pipeline_content}: {checking_result.message}')

                if checking_result.ill_typed:
                    logging.info(f'Pipeline {checking_result.pipeline_content} evaluated as ill-typed in {elapsed_time:.2f}s')
                else:
                    logging.info(f'Pipeline {checking_result.pipeline_content} evaluated as well-typed in {elapsed_time:.2f}s')
                pipeline_data_list.append(pipeline_data)
                
        except TimeoutError:
            pipeline_data = pipeline_data_template.copy()
            pipeline_data[CRASH_REASON_LABEL] = TIMEOUT_REASON
            pipeline_data["content"] = type_checker.get_current_pipeline_content_when_error()
            pipeline_data_list.append(pipeline_data)
            logging.warning(f'Pipeline evaluation timed out for {address}')
        except PashAnnotationParsingError as e:
            pipeline_data = pipeline_data_template.copy()
            pipeline_data["pash annotations error"] = str(e)
            pipeline_data["content"] = type_checker.get_current_pipeline_content_when_error()
            pipeline_data_list.append(pipeline_data)
            logging.error(f'Error while parsing annotations from {address}: {e}')

            
    except Exception as e:
        pipeline_data = pipeline_data_template.copy()
        pipeline_data[CRASH_REASON_LABEL] = str(e)
        pipeline_data["content"] = type_checker.get_current_pipeline_content_when_error()
        pipeline_data_list.append(pipeline_data)
        logging.error(f'Tool runtime error while evaluating pipeline from {address}: {e}')
    
    return pipeline_data_list

def process_pipeline(pipeline_info: Tuple[str, bool], evaluation_notes: List[dict], not_check_all_dirs: List[str]) -> List[dict]:
    address, label = pipeline_info
    check_all_pipelines = True
    file_dir = "/".join(address.split("/")[:-1])
    if file_dir in not_check_all_dirs:
        check_all_pipelines = False
    local_results = []
    for pipeline_result in evaluate_pipeline_content(address, check_all_pipelines):
        notes = notes_lookup(address, evaluation_notes, pipeline_result["content"]) or {CATEGORY_LABEL: "<missing>", "notes": ""}
        pipeline_result[IS_BUGGY_LABEL] = not label
        pipeline_result[CATEGORY_LABEL] = notes[CATEGORY_LABEL]
        pipeline_result["notes"] = notes["notes"]
        pipeline_result["tag"] = category_to_tag(notes[CATEGORY_LABEL])
        local_results.append(pipeline_result)
    return local_results

def add_parsing_failures_to_results(results, statistics):
    """Add failed parsing examples from logs to the results as false positives."""
    parsing_error_log_path = CONFIG.get("parsing_error_log_path")
    if not parsing_error_log_path or not os.path.exists(parsing_error_log_path):
        logging.warning(f"Parsing error log not found at {parsing_error_log_path}")
        return results, statistics
    
    logging.info(f"Reading parsing errors from {parsing_error_log_path}")
    
    # Read log file line by line to handle entries more accurately
    with open(parsing_error_log_path, 'r') as f:
        log_lines = f.readlines()
    
    if not log_lines:
        logging.info("Log file is empty, no parsing errors to process")
        return results, statistics
    
    # Process the log lines to construct entries
    entries = []
    current_entry = []
    for line in log_lines:
        # New entry starts with a timestamp
        if line.startswith('[20') and '] Error parsing file:' in line:
            if current_entry:
                entries.append(''.join(current_entry))
                current_entry = []
        current_entry.append(line)
    
    # Add the last entry if not empty
    if current_entry:
        entries.append(''.join(current_entry))
    
    logging.info(f"Found {len(entries)} error entries in the log")
    
    # Process each entry
    parsing_failures = []
    for entry_idx, entry in enumerate(entries):
        # Extract file path
        path_match = re.search(r'Error parsing file: (.+)\n', entry)
        if not path_match:
            logging.warning(f"Could not find file path in entry {entry_idx+1}")
            continue
        
        file_path = path_match.group(1).strip()
        logging.debug(f"Processing error entry {entry_idx+1} for file: {file_path}")
        
        # Find the content section
        if "File contents:" in entry:
            # Find the start of file contents
            start_idx = entry.find("File contents:") + len("File contents:")
            # Find the end (next timestamp or "Failed to read" or EOF)
            end_idx = len(entry)
            
            # Check for various end markers
            for marker in ["\n[20", "\nFailed to read", "\nFile not found"]:
                marker_idx = entry.find(marker, start_idx)
                if marker_idx != -1 and marker_idx < end_idx:
                    end_idx = marker_idx
            
            # Extract the content
            file_content = entry[start_idx:end_idx].strip()
            
            if file_content:
                preview = file_content[:50] + "..." if len(file_content) > 50 else file_content
                logging.debug(f"Successfully extracted content for {file_path}: {preview}")
            else:
                file_content = "Unknown"
                logging.warning(f"Empty content section for {file_path}")
        else:
            file_content = "Unknown"
            logging.warning(f"No 'File contents:' marker found for {file_path}")
        
        # Create a result entry
        pipeline_data = {
            IS_BUGGY_LABEL: False,  # Assuming it's a valid pipeline that failed to parse
            SIGNALED_LABEL: True,   # We're signaling an error
            CRASH_REASON_LABEL: "Parse failure",
            CATEGORY_LABEL: "parse fail",
            "tag": "parse_fail",
            "notes": "Pipeline failed during parsing phase",
            "tainted": True,
            "address": file_path,
            "content": file_content
        }
        
        # Add to results
        parsing_failures.append(pipeline_data)
    
    if parsing_failures:
        logging.info(f"Adding {len(parsing_failures)} parsing failures to results")
        # Log how many entries have content vs unknown
        known_content_count = sum(1 for p in parsing_failures if p["content"] != "Unknown")
        logging.info(f"  - {known_content_count} entries have extracted content")
        logging.info(f"  - {len(parsing_failures) - known_content_count} entries have unknown content")
        
        # Update statistics
        statistics["false_positives"] += len(parsing_failures)
        if "parse fail" in statistics["false_positive_categories"]:
            statistics["false_positive_categories"]["parse fail"] += len(parsing_failures)
        else:
            statistics["false_positive_categories"]["parse fail"] = len(parsing_failures)
        
        # Add to results
        results.extend(parsing_failures)
    
    return results, statistics

def run_all_evaluations(valid_dirs: list[str] = None,
                        invalid_dirs: list[str] = None,
                        output_json: str = None,
                        output_summary_csv: str = None,
                        evaluation_notes_json: str = None,
                        not_check_all_dirs: list[str] = None,
                        num_workers: int = None,
                        ):
    # Use CONFIG values as defaults
    valid_dirs = valid_dirs or CONFIG.get("valid_dirs", [])
    invalid_dirs = invalid_dirs or CONFIG.get("invalid_dirs", [])
    output_json = output_json or CONFIG.get("output_results_path", "evaluation_results/evaluation_results.json")
    output_summary_csv = output_summary_csv or CONFIG.get("output_summary_path", "evaluation_results/summary.csv")
    evaluation_notes_json = evaluation_notes_json or CONFIG.get("evaluation_notes_path", "src/stream/evaluation_notes.json")
    not_check_all_dirs = not_check_all_dirs or CONFIG.get("not_check_all_dirs", [])
    num_workers = num_workers or CONFIG.get("num_workers", 1)
    
    # Clear the parsing error log file before starting
    parsing_error_log_path = CONFIG.get("parsing_error_log_path")
    if parsing_error_log_path:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(parsing_error_log_path), exist_ok=True)
        # Clear or create the log file
        with open(parsing_error_log_path, 'w') as f:
            f.write("")
        logging.info(f"Cleared parsing error log at {parsing_error_log_path}")
    
    with open(evaluation_notes_json, 'r') as f:
        evaluation_notes = json.load(f)

    pipelines: list[tuple[str, bool]] = []
    start_time_total = time.time()
    
    valid_pipelines = find_scripts(valid_dirs)
    invalid_pipelines = find_scripts(invalid_dirs)
    pipelines.extend(zip(valid_pipelines, [True] * len(valid_pipelines)))
    pipelines.extend(zip(invalid_pipelines, [False] * len(invalid_pipelines)))
    
    if not pipelines:
        logging.error("No pipelines found")
        return

    results = []
    if num_workers > 1:
        logging.info(f"Running in parallel mode with {num_workers} workers")
        with multiprocessing.Pool(processes=num_workers) as pool:
            worker_func = partial(process_pipeline, evaluation_notes=evaluation_notes, not_check_all_dirs=not_check_all_dirs)
            result_lists = pool.map(worker_func, pipelines)
        results = [r for sublist in result_lists for r in sublist]
    else:
        logging.info("Running in sequential mode")
        for address, label in pipelines:
            check_all_pipelines = True
            file_dir = "/".join(address.split("/")[:-1])
            if file_dir in not_check_all_dirs:
                check_all_pipelines = False
            for pipeline_result in evaluate_pipeline_content(address, check_all_pipelines):
                notes = notes_lookup(address, evaluation_notes, pipeline_result["content"]) or {CATEGORY_LABEL: "<missing>", "notes": ""}
                pipeline_result[IS_BUGGY_LABEL] = not label
                pipeline_result[CATEGORY_LABEL] = notes[CATEGORY_LABEL]
                pipeline_result["notes"] = notes["notes"]
                pipeline_result["tag"] = category_to_tag(notes[CATEGORY_LABEL])
                results.append(pipeline_result)

    unlabeled_inconsistent_results = [
        result for result in results 
        if result[IS_BUGGY_LABEL] != result[SIGNALED_LABEL] and result[CATEGORY_LABEL] == "<missing>"
    ]

    labeled_inconsistent_results = [
        result for result in results 
        if result[IS_BUGGY_LABEL] != result[SIGNALED_LABEL] and result[CATEGORY_LABEL] != "<missing>"
    ]

    failures = [result for result in results if result[IS_BUGGY_LABEL] != result[SIGNALED_LABEL]]
    crash_pipelines = [r for r in failures if r[SIGNALED_LABEL] == None]
    timeout_pipelines =      [r for r in crash_pipelines if r[CRASH_REASON_LABEL] == TIMEOUT_REASON]
    valid_pipeline_crashes = [r for r in crash_pipelines if not r[IS_BUGGY_LABEL] and (r[CRASH_REASON_LABEL] != None or r["pash annotations error"] != None)]
    buggy_pipeline_crashes = [r for r in crash_pipelines if     r[IS_BUGGY_LABEL] and (r[CRASH_REASON_LABEL] != None or r["pash annotations error"] != None)]
    false_positive_pipelines = [r for r in failures if not r[IS_BUGGY_LABEL] and r[SIGNALED_LABEL] != None]
    false_negative_pipelines = [r for r in failures if     r[IS_BUGGY_LABEL] and r[SIGNALED_LABEL] != None]

    # Count tainted pipelines
    untainted_pipelines = [r for r in results if r.get("tainted") == False]

    total_false_positives = len(false_positive_pipelines)
    total_false_negatives = len(false_negative_pipelines)
    total_correct_pipeline_crashes = len(valid_pipeline_crashes)
    total_buggy_pipeline_crashes = len(buggy_pipeline_crashes)
    total_timeouts = len(timeout_pipelines)
    total_correct_pipelines = sum(1 for r in results if not r[IS_BUGGY_LABEL])
    total_buggy_pipelines = sum(1 for r in results if r[IS_BUGGY_LABEL])
    
    preds = [result[SIGNALED_LABEL] for result in results if result[CRASH_REASON_LABEL] != TIMEOUT_REASON]
    labels = [result[IS_BUGGY_LABEL] for result in results if result[CRASH_REASON_LABEL] != TIMEOUT_REASON]
    
    statistics = {}
    if preds and labels:
        statistics.update({
            "accuracy": calculate_accuracy(labels, preds),
            "precision": calculate_precision(labels, preds),
            "recall": calculate_recall(labels, preds),
        })

        logging.info(f'Accuracy: {statistics["accuracy"]}')
        logging.info(f'Precision: {statistics["precision"]}')
        logging.info(f'Recall: {statistics["recall"]}')
        logging.info(f'Total timeouts: {total_timeouts}')
        logging.info(f'Crashes (including timeouts): {total_correct_pipeline_crashes + total_buggy_pipeline_crashes}')
        logging.info(f'Untainted pipelines: {len(untainted_pipelines)}')
    end_time_total = time.time()
    total_time = end_time_total - start_time_total

    output_data = {
        "unlabeled_inconsistent_results": unlabeled_inconsistent_results,
        "labeled_inconsistent_results": labeled_inconsistent_results,
        "evaluation_results": results,
        "statistics": {
            **statistics,

            "total_pipelines": len(results),

            "timeout_count": total_timeouts,
            "crashes": total_buggy_pipeline_crashes + total_correct_pipeline_crashes,
            "correct_crashes": total_correct_pipeline_crashes,
            "buggy_crashes": total_buggy_pipeline_crashes,
            "total_correct_pipelines": total_correct_pipelines,
            "false_positives": total_false_positives,
            "false_positive_categories": categorize(false_positive_pipelines),
            "total_buggy_pipelines": total_buggy_pipelines,
            "false_negatives": total_false_negatives,
            "false_negative_categories": categorize(false_negative_pipelines),
            "total_wrong_predictions": total_false_positives + total_false_negatives,
            
            "untainted_pipelines": len(untainted_pipelines),

            "total_evaluation_time": f"{total_time:.2f}s",
        },
        # "logs": log_handler.log_entries
    }
    
    # Add parsing failures to results
    results, output_data["statistics"] = add_parsing_failures_to_results(results, output_data["statistics"])
    
    # Recalculate failures after adding parsing errors
    failures = [result for result in results if result[IS_BUGGY_LABEL] != result[SIGNALED_LABEL]]
    false_positive_pipelines = [r for r in failures if not r[IS_BUGGY_LABEL] and r[SIGNALED_LABEL] != None]
    output_data["statistics"]["total_wrong_predictions"] = len(failures)
    output_data["statistics"]["false_positive_categories"] = categorize(false_positive_pipelines)

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, 'w') as json_file:
        json.dump(output_data, json_file, indent=4)
    logging.info(f"Results written to {output_json}")
    with open(output_summary_csv, 'w') as csv:
        tabulate(output_data['statistics'], csv)
    logging.info(f"Summary table written to {output_summary_csv}; format with `column -s, -t {output_summary_csv}`")
    logging.info(f"Total evaluation time: {total_time:.2f}s")

def categorize(results, category_label=CATEGORY_LABEL):
    categories = {}
    for r in results:
        if r[category_label] in categories:
            categories[r[category_label]] += 1
        else:
            categories[r[category_label]]  = 1
    return categories

# TODO: might be nice to put this in a separate module to tabulate already-existing results
def tabulate(result_stats, f):
    s = result_stats
    f.write("category,total,crash,signaled,false (pos/neg),category, tag\n")
    f.write("========,=====,=====,========,===============,========,========\n")
    f.write(f"correct,{s['total_correct_pipelines']},{s['correct_crashes']},{s['false_positives']},{s['false_positives']},, \n")
    for category, count in s['false_positive_categories'].items():
        f.write(f" , , , ,{count},{category.replace(',', ';')},{category_to_tag(category)}\n")
    f.write("--------,-----,-----,--------,---------------,--------,--------\n")
    buggy_signals = s['total_buggy_pipelines'] - s['false_negatives'] - s['buggy_crashes']
    f.write(f"buggy,{s['total_buggy_pipelines']},{s['buggy_crashes']},{buggy_signals},{s['false_negatives']},, \n")
    for category, count in s['false_negative_categories'].items():
        f.write(f" , , , ,{count},{category.replace(',', ';')},{category_to_tag(category)}\n")
    f.write("========,=====,=====,========,===============,========,========\n")
    f.write(f"total,{s['total_pipelines']},{s['crashes']}, ,{s['false_positives'] + s['false_negatives']},, \n")

def merge_notes(notes_to_merge: List[dict]) -> dict:
    if not notes_to_merge:
        return {}

    merged_note = {}
    for note in notes_to_merge:
        for key, value in note.items():
            if key not in merged_note or merged_note[key] == None or merged_note[key] == "":
                merged_note[key] = value
            else:
                if key == "category":
                    if (merged_note[key] == "<missing>" or merged_note[key] == "") and (value == "<missing>" or value == ""):
                        merged_note[key] = "<missing>"
                    elif (merged_note[key] == "<missing>" or merged_note[key] == "") or (value == "<missing>" or value == ""):
                        merged_note[key] = value if (value != "<missing>" and value != "") else merged_note[key]
                    else:
                        print(f"Warning: Conflict in 'category' field. Keeping later value. All notes: {notes_to_merge}")
                        merged_note[key] = value
                else:
                    if merged_note[key] != value:
                        print(f"Warning: Conflict in field '{key}'. Keeping later value. All notes: {notes_to_merge}")
                    merged_note[key] = value

    return merged_note


# listof(Note) content -> Optional(Note)
def notes_lookup(address, notes: List[dict], content):
    matching_notes = []
    complete_matching_notes = []

    if "full_benchmark/llm_injection" in address:
        for note in notes:
            if note.get("address", "") == address:
                matching_notes.append(note)
    else:
        for note in notes:
            if note.get("content", "") == content:
                if note.get("address", "") == address:
                    complete_matching_notes.append(note)
                else:
                    matching_notes.append(note)

    if not matching_notes and not complete_matching_notes:
        return None

    if complete_matching_notes:
        merged_note = merge_notes(complete_matching_notes)
    else:
        merged_note = merge_notes(matching_notes)
    return merged_note

def category_to_tag(category: str):
    with open("./src/stream/category_to_tag.json", "r") as file:
        mapping = json.load(file)
    mapping.sort(key=lambda x: x["priority"])
    for entry in mapping:
        if entry["category"] in category:
            return entry["tag"]
    return ""


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Run benchmarks.')
    parser.add_argument('--disable_annotation', action='store_true',
                        help='Disable user annotation handling. Defaults to enabled.')
    parser.add_argument('--log_level', default=None, type=str, 
                        help='Set logging level: info, debug, error.')
    parser.add_argument('--timeout', default=None, type=int,
                        help='Set pipeline evaluation timeout in seconds.')
    parser.add_argument('--workers', default=None, type=int,
                        help='Number of parallel workers (set 1 to disable parallelism).')
    
    # Add heuristic rule arguments
    parser.add_argument('--disable_rule_no_empty_output', action='store_true',
                        help='Disable the rule that checks for empty output.')
    parser.add_argument('--disable_rule_no_ignored_input', action='store_true',
                        help='Disable the rule that checks for ignored input.')
    parser.add_argument('--disable_rule_no_space_in_file_name', action='store_true',
                        help='Disable the rule that checks for spaces in file names.')
    parser.add_argument('--disable_rule_no_meaningless_command', action='store_true',
                        help='Disable the rule that checks for meaningless commands.')
    parser.add_argument('--disable_rule_no_sort_non_numeric_with_numeric_input', action='store_true',
                        help='Disable the rule that checks for numeric sorting of non-numeric data.')

    parser.add_argument('--disable_fsts', action='store_true',
                        help='Disable FSTs. Defaults to enabled.')
    parser.add_argument('--outdir', default=None, type=str,
                        help='Output directory, to override whatever is in the global_config.yaml (but using the same file names)')

    args = parser.parse_args()

    # Override CONFIG with command line args
    if args.disable_annotation:
        enable_user_annotation = False
        CONFIG["enable_user_annotation"] = False
    else:
        enable_user_annotation = CONFIG.get("enable_user_annotation", True)

    if args.disable_fsts:
        CONFIG["enable_FST"] = False

    if args.log_level:
        level_str = args.log_level.lower()
        if level_str == "debug":
            level = logging.DEBUG
        elif level_str == "error":
            level = logging.WARNING
        else:
            level = logging.INFO
        CONFIG["log_level"] = level_str
    else:
        level_str = CONFIG.get("log_level", "INFO").lower()
        if level_str == "debug":
            level = logging.DEBUG
        elif level_str == "error":
            level = logging.WARNING
        else:
            level = logging.INFO

    if args.timeout is not None:
        TIMEOUT_SECONDS = args.timeout
        CONFIG["timeout_seconds"] = args.timeout
        if TIMEOUT_SECONDS > 0:
            ENABLE_TIMEOUT = True
            CONFIG["enable_timeout"] = True
            TIMEOUT_REASON = f"Timeout after {TIMEOUT_SECONDS}s"
        else:
            ENABLE_TIMEOUT = False
            CONFIG["enable_timeout"] = False
    else:
        ENABLE_TIMEOUT = CONFIG.get("enable_timeout", False)
        TIMEOUT_SECONDS = CONFIG.get("timeout_seconds", 10)
        if ENABLE_TIMEOUT:
            TIMEOUT_REASON = f"Timeout after {TIMEOUT_SECONDS}s"

    if args.workers is not None:
        workers = args.workers
        CONFIG["num_workers"] = args.workers
    else:
        workers = CONFIG.get("num_workers", 1)

    # Handle heuristic rule command line arguments
    if args.disable_rule_no_empty_output:
        CONFIG["enable_rule_no_empty_output"] = False
    if args.disable_rule_no_ignored_input:
        CONFIG["enable_rule_no_ignored_input"] = False
    # if args.disable_rule_no_space_in_file_name:
    #     CONFIG["enable_rule_no_space_in_file_name"] = False
    if args.disable_rule_no_meaningless_command:
        CONFIG["enable_rule_no_meaningless_command"] = False
    if args.disable_rule_no_sort_non_numeric_with_numeric_input:
        CONFIG["enable_rule_no_sort_non_numeric_with_numeric_input"] = False
        
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Enable user annotation: {enable_user_annotation}")
    logging.info(f"Logging level: {level_str}")
    if ENABLE_TIMEOUT:
        logging.info(f"Timeout set to: {TIMEOUT_SECONDS} seconds")
    else:
        logging.info("Timeout disabled")
    logging.info(f"Number of workers: {workers}")
    
    # Log heuristic rule settings
    logging.info(f"Rule no_empty_output: {CONFIG.get('enable_rule_no_empty_output', True)}")
    logging.info(f"Rule no_ignored_input: {CONFIG.get('enable_rule_no_ignored_input', True)}")
    # logging.info(f"Rule no_space_in_file_name: {CONFIG.get('enable_rule_no_space_in_file_name', True)}")
    logging.info(f"Rule no_meaningless_command: {CONFIG.get('enable_rule_no_meaningless_command', True)}")
    logging.info(f"Rule no_sort_non_numeric_with_numeric_input: {CONFIG.get('enable_rule_no_sort_non_numeric_with_numeric_input', True)}")

    logging.getLogger().setLevel(level)

    time.sleep(3)

    # Use config values for the paths
    if args.outdir:
        CONFIG.set("output_results_path_with_annotation",
                   os.path.join(args.outdir, os.path.basename(CONFIG.get("output_results_path_with_annotation"))))
        CONFIG.set("output_results_path_raw",
                   os.path.join(args.outdir, os.path.basename(CONFIG.get("output_results_path_raw"))))
    
    run_all_evaluations(
        num_workers=workers,
        output_json=CONFIG["output_results_path_with_annotation"] if enable_user_annotation else CONFIG["output_results_path_raw"],
        output_summary_csv=CONFIG["output_summary_path_with_annotation"] if enable_user_annotation else CONFIG["output_summary_path_raw"]
    )
    jpype.shutdownJVM()
