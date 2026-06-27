import multiprocessing
import os
import json
import logging
import time
import re
import traceback
import contextlib
import sys
from functools import partial
from pathlib import Path
from typing import List, TextIO, Tuple
from tqdm import tqdm

from stream.utils.timing import Timing
from stream.type_checker import ScriptChecker
from stream.parser.shell_parser_util import extract_pipe_nodes_from_file
from stream.tool_error import PashAnnotationParsingError, TimeoutError
from stream.utils.format import pretty_ast_node
import argparse
from stream.config import CONFIG
import csv

ENABLE_TIMEOUT = CONFIG.get("enable_timeout", False)
TIMEOUT_SECONDS = CONFIG.get("timeout_seconds", 10)

IS_BUGGY_LABEL = "is buggy?"
SIGNALED_LABEL = "warning signaled?"
PIPELINE_ID_LABEL = "id"
CATEGORY_LABEL = "category"
CRASH_REASON_LABEL = "tool runtime error"
CRASH_TYPE_LABEL = "tool runtime error type"
CRASH_TRACEBACK_LABEL = "tool runtime traceback"
PASH_TRACEBACK_LABEL = "pash annotations traceback"
TIMEOUT_REASON = f"Timeout after {TIMEOUT_SECONDS}s"
RUNTIME_ERROR_LOG_FILENAME = "runtime_errors.log"

enable_user_annotation = CONFIG.get("enable_user_annotation", True)

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
    "ladder": "LadderTypes",
    "handwritten": "Handwritten",
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


def infer_benchmark_name(address: str) -> str:
    normalized_address = normalize_result_path(address).lstrip("./")
    benchmark_patterns = CONFIG.get("benchmark names", {})
    for pattern, name in benchmark_patterns.items():
        if re.match(pattern, normalized_address):
            return BENCHMARK_CATEGORY_ALIASES.get(str(name), str(name))

    parts = Path(normalized_address).parts
    if "full_benchmark" in parts:
        index = parts.index("full_benchmark")
        if index + 1 < len(parts):
            return BENCHMARK_CATEGORY_ALIASES.get(parts[index + 1], parts[index + 1])
    return parts[0] if parts else "unknown"


def count_pipelines_by_category(pipelines: list[tuple[str, bool]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for address, _ in pipelines:
        category = infer_benchmark_name(address)
        counts[category] = counts.get(category, 0) + 1
    return counts


def group_pipelines_by_category(pipelines: list[tuple[str, bool]]) -> list[tuple[str, bool]]:
    return sorted(
        pipelines,
        key=lambda item: (
            BENCHMARK_PROGRAM_ORDER.get(infer_benchmark_name(item[0]), len(BENCHMARK_PROGRAM_ORDER)),
            normalize_result_path(item[0]),
        ),
    )


def benchmark_program_totals_for(pipelines: list[tuple[str, bool]]) -> dict[str, int]:
    categories = {infer_benchmark_name(address) for address, _ in pipelines}
    return {
        category: BENCHMARK_PROGRAM_TOTALS[category]
        for category in BENCHMARK_PROGRAM_TOTALS
        if category in categories
    }


def check_all_pipelines_for_address(address: str, not_check_all_dirs: list[str]) -> bool:
    file_dir = "/".join(address.split("/")[:-1])
    return file_dir not in not_check_all_dirs


def extract_progress_pipeline_strings(address: str, check_all_pipelines: bool) -> list[str]:
    extract_all_pipelines = check_all_pipelines
    if extract_all_pipelines:
        try:
            with open(address, "r", encoding="utf-8") as handle:
                first_two_lines = [handle.readline().strip(), handle.readline().strip()]
            if any("# stream disable" in line for line in first_two_lines):
                extract_all_pipelines = False
        except OSError as error:
            logging.warning(f"Failed to read {address} while preparing progress totals: {error}")

    try:
        pipeline_nodes = extract_pipe_nodes_from_file(address, extract_all_pipelines)
    except Exception as error:
        logging.warning(f"Failed to pre-extract pipelines from {address}: {error}")
        return []

    if not extract_all_pipelines:
        pipeline_nodes = [node for node, _ in pipeline_nodes]

    return [pretty_ast_node(node) for node in pipeline_nodes]


def unique_program_keys_by_category(
    pipelines: list[tuple[str, bool]],
    not_check_all_dirs: list[str],
) -> dict[str, set[tuple[str, str]]]:
    keys: dict[str, set[tuple[str, str]]] = {}
    for address, _ in pipelines:
        category = infer_benchmark_name(address)
        keys.setdefault(category, set())
        check_all_pipelines = check_all_pipelines_for_address(address, not_check_all_dirs)
        for pipeline_content in extract_progress_pipeline_strings(address, check_all_pipelines):
            keys[category].add((normalize_result_path(address), pipeline_content))
    return keys


def count_unique_program_keys_by_category(keys: dict[str, set[tuple[str, str]]]) -> dict[str, int]:
    return {category: len(contents) for category, contents in keys.items() if contents}


def restore_result_order(results: list[dict], pipelines: list[tuple[str, bool]]) -> list[dict]:
    order = {address: index for index, (address, _) in enumerate(pipelines)}
    return sorted(results, key=lambda result: order.get(result.get("address", ""), len(order)))


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


def annotations_enabled_for_path(address: str) -> bool:
    if not enable_user_annotation:
        return False

    disabled_dirs = CONFIG.get("annotation_disabled_dirs", [])
    if not disabled_dirs:
        return True

    address_path = Path(address)
    if not address_path.is_absolute():
        address_path = Path(CONFIG.PROJECT_ROOT) / address_path
    address_path = address_path.resolve(strict=False)

    for disabled_dir in disabled_dirs:
        disabled_path = Path(disabled_dir)
        if not disabled_path.is_absolute():
            disabled_path = Path(CONFIG.PROJECT_ROOT) / disabled_path
        disabled_path = disabled_path.resolve(strict=False)

        try:
            address_path.relative_to(disabled_path)
            return False
        except ValueError:
            continue

    return True

def find_scripts(directories: list[str]) -> list[str]:
    script_addresses = []
    
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.sh')) or file.endswith(('.bash')) or file.endswith(('.zsh')):
                    file_path = os.path.join(root, file)
                    script_addresses.append(file_path)
    
    return script_addresses


def get_current_pipeline_content_when_error(type_checker) -> str | None:
    if type_checker is None:
        return None

    try:
        return type_checker.get_current_pipeline_content_when_error()
    except Exception as capture_error:
        logging.warning(f"Failed to capture current pipeline content after runtime error: {capture_error}")
        return None


def write_runtime_errors_to_file(results: List[dict], output_path: str) -> None:
    runtime_errors = [
        result for result in results
        if result.get(CRASH_TRACEBACK_LABEL) or result.get(PASH_TRACEBACK_LABEL)
    ]

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        if not runtime_errors:
            handle.write("No runtime errors captured.\n")
            logging.info(f"No runtime errors captured; wrote empty report to {output_path}")
            return

        for index, result in enumerate(runtime_errors, start=1):
            error_kind = "pash annotations error" if result.get(PASH_TRACEBACK_LABEL) else CRASH_REASON_LABEL
            error_message = result.get("pash annotations error") if result.get(PASH_TRACEBACK_LABEL) else result.get(CRASH_REASON_LABEL, "<unknown>")
            traceback_text = result.get(PASH_TRACEBACK_LABEL) or result.get(CRASH_TRACEBACK_LABEL) or ""
            handle.write(f"Runtime error #{index}\n")
            handle.write(f"Address: {result.get('address', '<unknown>')}\n")
            handle.write(f"Pipeline: {result.get('content') or '<unknown>'}\n")
            handle.write(f"Error kind: {error_kind}\n")
            handle.write(f"Exception type: {result.get(CRASH_TYPE_LABEL, '<unknown>')}\n")
            handle.write(f"Error: {error_message}\n")
            handle.write("Traceback:\n")
            handle.write(traceback_text)
            if not traceback_text.endswith("\n"):
                handle.write("\n")
            handle.write("\n" + ("=" * 80) + "\n\n")

    logging.info(f"Wrote {len(runtime_errors)} runtime error tracebacks to {output_path}")


# Functional filters for result classification
def is_timeout(result):
    """Filter for timeout cases"""
    return result.get(CRASH_REASON_LABEL) == TIMEOUT_REASON

def is_true_positive(result):
    """Filter for True Positive cases: buggy and warning signaled"""
    return result.get("is buggy?") and result.get("warning signaled?")

def is_true_negative(result):
    """Filter for True Negative cases: not buggy and no warning signaled"""
    return not result.get("is buggy?") and not result.get("warning signaled?")

def is_false_positive(result):
    """Filter for False Positive cases: not buggy but warning signaled (exclude crashes)"""
    return (not result.get("is buggy?") and 
            result.get("warning signaled?") is True)

def is_false_negative(result):
    """Filter for False Negative cases: buggy but no warning signaled (exclude crashes)"""
    return (result.get("is buggy?") and 
            result.get("warning signaled?") is False)

def is_correct_prediction(result):
    """Filter for correct predictions (TP + TN)"""
    return result.get("is buggy?") == result.get("warning signaled?")

def is_incorrect_prediction(result):
    """Filter for incorrect predictions (FP + FN)"""
    return result.get("is buggy?") != result.get("warning signaled?")

def is_crash(result):
    """Filter for crash cases where warning signaled is None"""
    return result.get("warning signaled?") is None

def is_valid_pipeline_crash(result):
    """Filter for crashes in valid pipelines (not buggy but crashed)"""
    return (is_crash(result) and 
            not result.get("is buggy?") and 
            (result.get(CRASH_REASON_LABEL) is not None or result.get("pash annotations error") is not None))

def is_buggy_pipeline_crash(result):
    """Filter for crashes in buggy pipelines"""
    return (is_crash(result) and 
            result.get("is buggy?") and 
            (result.get(CRASH_REASON_LABEL) is not None or result.get("pash annotations error") is not None))

def is_buggy_pipeline(result):
    """Filter for buggy pipelines"""
    return result.get("is buggy?")

def is_valid_pipeline(result):
    """Filter for valid (non-buggy) pipelines"""
    return not result.get("is buggy?")

def is_untainted(result):
    """Filter for untainted pipelines"""
    return result.get("tainted") == False

def has_result_category(result):
    """Whether the result has a human diagnosis category attached."""
    return result.get(CATEGORY_LABEL) not in (None, "", "<missing>")

def calculate_accuracy_functional(results):
    """Calculate accuracy using functional approach"""
    # Filter out timeout cases
    valid_results = [r for r in results if not is_timeout(r)]
    
    if not valid_results:
        return 0.0
    
    # Count correct predictions
    correct_count = len([r for r in valid_results if is_correct_prediction(r)])
    
    return correct_count / len(valid_results)

def calculate_precision_functional(results):
    """Calculate precision using functional approach"""
    valid_results = [r for r in results if not is_timeout(r)]
    
    true_positives = [r for r in valid_results if is_true_positive(r)]
    false_positives = [r for r in valid_results if is_false_positive(r)]

    denominator = len(true_positives) + len(false_positives)
    if denominator == 0:
        return 0.0
    
    return len(true_positives) / denominator

def calculate_recall_functional(results):
    """Calculate recall using functional approach"""
    valid_results = [r for r in results if not is_timeout(r)]
    
    true_positives = [r for r in valid_results if is_true_positive(r)]
    false_negatives = [r for r in valid_results if is_false_negative(r)]
    
    denominator = len(true_positives) + len(false_negatives)
    if denominator == 0:
        return 0.0
    
    return len(true_positives) / denominator







def evaluate_pipeline_content(address: str, check_all_pipelines: bool, label: bool) -> list[dict]:
    pipeline_data_template = {
        "address": address,
        "content": None,
        IS_BUGGY_LABEL: None,
        SIGNALED_LABEL: None,
        CRASH_REASON_LABEL: None,
        CRASH_TYPE_LABEL: None,
        CRASH_TRACEBACK_LABEL: None,
        "pash annotations error": None,
        PASH_TRACEBACK_LABEL: None,
        "error message generated": None,
        "error_results": [],  # Add field to store detailed error results
        "evaluation_time": "0s",  # Default to 0s for evaluation time
        "tainted": None,
        "pipeline_length": 0,     # Track pipeline length
        "automata_size": 0,       # Track automata size
        # "notes": ""
    }
    pipeline_data_list = []
    type_checker = None
    
    try:        
        logging.info(f"Evaluating pipeline from {address}")
        enable_annotations_for_path = annotations_enabled_for_path(address)
        if enable_user_annotation and not enable_annotations_for_path:
            logging.info(f"User annotations disabled for {address} based on path configuration")
        type_checker = ScriptChecker(
            address, 
            enable_user_annotations=enable_annotations_for_path,
            enable_stage_timeout=ENABLE_TIMEOUT, 
            stage_timeout=TIMEOUT_SECONDS, 
            check_all_pipelines=check_all_pipelines,
            enable_rule_no_empty_output=CONFIG.get("enable_rule_no_empty_output", True),
            enable_rule_no_ignored_input=CONFIG.get("enable_rule_no_ignored_input", True),
            enable_rule_no_meaningless_command=CONFIG.get("enable_rule_no_meaningless_command", True),
            enable_rule_no_sort_non_numeric_with_numeric_input=CONFIG.get("enable_rule_no_sort_non_numeric_with_numeric_input", True),
            label=label,
            enable_concretization=CONFIG.get("enable_concretization", True)
        )

        try:
            while True:
                start_time = time.time()
                logging.debug(f'Evaluating pipeline from {address}')
                checking_result = type_checker.check_next()
                if checking_result is None:
                    break

                end_time = time.time()
                elapsed_time = max(0, end_time - start_time - checking_result.statistics_time)

                pipeline_data = pipeline_data_template.copy()
                pipeline_data["content"] = checking_result.pipeline_content
                pipeline_data["evaluation_time"] = f"{elapsed_time:.8f}s"
                pipeline_data["automata_size"] = checking_result.max_automata_size
                pipeline_data["pipeline_length"] = checking_result.pipeline_length
                pipeline_data["self_contained"] = checking_result.self_contained
                
                # Convert ErrorResult objects to dictionaries for JSON serialization
                error_results_dicts = []
                for error_result in checking_result.error_results:
                    error_dict = {
                        "message": error_result.message,
                        "witness": error_result.witness,
                        # "derivation_trace": error_result.derivation_trace,
                        "all_input": error_result.all_input,
                        "serious_violation": error_result.serious_violation,
                        "command_name": error_result.command_name,
                        "better_witness": error_result.better_witness,
                        "command_index": error_result.command_index,
                        # "tainted": error_result.tainted
                    }
                    error_results_dicts.append(error_dict)
                pipeline_data["error_results"] = error_results_dicts

                if checking_result.runtime_error_message is not None:
                    pipeline_data[CRASH_TYPE_LABEL] = checking_result.runtime_error_type
                    if checking_result.runtime_error_kind == "pash annotations error":
                        pipeline_data["pash annotations error"] = checking_result.runtime_error_message
                        pipeline_data[PASH_TRACEBACK_LABEL] = checking_result.runtime_error_traceback
                        logging.error(
                            f'Pash annotation parsing error in pipeline {checking_result.pipeline_content}: '
                            f'{checking_result.runtime_error_message}'
                        )
                    else:
                        pipeline_data[CRASH_REASON_LABEL] = checking_result.runtime_error_message
                        pipeline_data[CRASH_TRACEBACK_LABEL] = checking_result.runtime_error_traceback
                        logging.error(
                            f'Tool runtime error in pipeline {checking_result.pipeline_content}: '
                            f'{checking_result.runtime_error_message}'
                        )
                    pipeline_data_list.append(pipeline_data)
                    continue

                pipeline_data[SIGNALED_LABEL] = len(checking_result.error_results) > 0
                
                # pipeline_data["tainted"] = checking_result.tainted
                if len(checking_result.error_results) > 0:
                    pipeline_data["error message generated"] = checking_result.error_results[0].message
                    logging.info(f'Error detected in pipeline {checking_result.pipeline_content}: {checking_result.error_results[0].message}')
                    # pipeline_data["tainted"] = checking_result.error_results[0].tainted

                if len(checking_result.error_results) > 0:
                    logging.info(f'Pipeline {checking_result.pipeline_content} evaluated as ill-typed in {elapsed_time:.2f}s')
                else:
                    logging.info(f'Pipeline {checking_result.pipeline_content} evaluated as well-typed in {elapsed_time:.2f}s')

                pipeline_data_list.append(pipeline_data)
                
        except TimeoutError:
            pipeline_data = pipeline_data_template.copy()
            pipeline_data[CRASH_REASON_LABEL] = TIMEOUT_REASON
            pipeline_data["content"] = get_current_pipeline_content_when_error(type_checker)
            pipeline_data_list.append(pipeline_data)
            logging.warning(f'Pipeline evaluation timed out for {address}')
        except PashAnnotationParsingError as e:
            pipeline_data = pipeline_data_template.copy()
            pipeline_data["pash annotations error"] = str(e)
            pipeline_data[CRASH_TYPE_LABEL] = type(e).__name__
            pipeline_data[PASH_TRACEBACK_LABEL] = traceback.format_exc()
            pipeline_data["content"] = get_current_pipeline_content_when_error(type_checker)
            pipeline_data_list.append(pipeline_data)
            logging.exception(f'Error while parsing annotations from {address}: {e}')

            
    except Exception as e:
        pipeline_data = pipeline_data_template.copy()
        pipeline_data[CRASH_REASON_LABEL] = str(e)
        pipeline_data[CRASH_TYPE_LABEL] = type(e).__name__
        pipeline_data[CRASH_TRACEBACK_LABEL] = traceback.format_exc()
        pipeline_data["content"] = get_current_pipeline_content_when_error(type_checker)
        pipeline_data_list.append(pipeline_data)
        logging.exception(f'Tool runtime error while evaluating pipeline from {address}: {e}')
    
    return pipeline_data_list

def add_result_metadata(pipeline_result: dict, label: bool) -> None:
    pipeline_result[IS_BUGGY_LABEL] = not label
    pipeline_result[CATEGORY_LABEL] = ""
    pipeline_result["notes"] = ""
    pipeline_result["tag"] = ""


def process_pipeline(pipeline_info: Tuple[str, bool], not_check_all_dirs: List[str]) -> List[dict]:
    address, label = pipeline_info
    check_all_pipelines = True
    file_dir = "/".join(address.split("/")[:-1])
    if file_dir in not_check_all_dirs:
        check_all_pipelines = False
    local_results = []
    for pipeline_result in evaluate_pipeline_content(address, check_all_pipelines, label):
        add_result_metadata(pipeline_result, label)
        local_results.append(pipeline_result)
    return local_results

def normalize_result_path(path: str) -> str:
    if not path:
        return path

    normalized = path.strip()
    if os.path.isabs(normalized):
        try:
            normalized = os.path.relpath(normalized, os.getcwd())
        except ValueError:
            return normalized

    normalized = normalized.replace(os.sep, "/")
    if not normalized.startswith("./"):
        normalized = f"./{normalized}"
    return normalized


def infer_benchmark_bug_label(address: str) -> bool | None:
    normalized_address = normalize_result_path(address)

    for directory in CONFIG.get("valid_dirs", []):
        normalized_dir = normalize_result_path(directory).rstrip("/")
        if normalized_address == normalized_dir or normalized_address.startswith(f"{normalized_dir}/"):
            return False

    for directory in CONFIG.get("invalid_dirs", []):
        normalized_dir = normalize_result_path(directory).rstrip("/")
        if normalized_address == normalized_dir or normalized_address.startswith(f"{normalized_dir}/"):
            return True

    return None


def add_parsing_failures_to_results(results, statistics):
    """Add parser-failed benchmark pipelines to the results as no-warning rows."""
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
        if file_path.startswith("/tmp"):
            logging.warning(f"Skipping temporary parser error with no benchmark source path: {file_path}")
            continue
        file_path = normalize_result_path(file_path)
        is_buggy = infer_benchmark_bug_label(file_path)
        if is_buggy is None:
            logging.warning(f"Skipping parser error outside configured benchmark dirs: {file_path}")
            continue
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
            IS_BUGGY_LABEL: is_buggy,
            SIGNALED_LABEL: False,  # Parser failures do not report a bug.
            CRASH_REASON_LABEL: "Parse failure",
            CATEGORY_LABEL: "parse fail",
            "tag": "parse_fail",
            "notes": "Pipeline failed during parsing phase; RT emitted no bug report.",
            "tainted": True,
            "address": file_path,
            "content": file_content,
            "error_results": [],     # No detailed error results for parse failures
            "evaluation_time": "0s",  # Set evaluation time to 0 for parse failures
            "automata_size": 0,       # No automata for parse failures
            "pipeline_length": 0      # No valid pipeline length for parse failures
        }
        
        # Add to results
        parsing_failures.append(pipeline_data)
    
    if parsing_failures:
        logging.info(f"Adding {len(parsing_failures)} parsing failures to results")
        # Log how many entries have content vs unknown
        known_content_count = sum(1 for p in parsing_failures if p["content"] != "Unknown")
        logging.info(f"  - {known_content_count} entries have extracted content")
        logging.info(f"  - {len(parsing_failures) - known_content_count} entries have unknown content")
        
        # Add to results
        results.extend(parsing_failures)
    
    return results, statistics

def deduplicate_results(results):
    """
    Deduplicate evaluation results based on identical address and content.
    Returns a new list with duplicates removed, keeping the first occurrence.
    """
    seen = set()
    deduplicated = []

    for result in results:
        identifier = (result.get("address", ""), result.get("content", ""))

        if identifier not in seen:
            seen.add(identifier)
            deduplicated.append(result)
        else:
            logging.info(
                f"Removing duplicate result with address: {result.get('address')} "
                f"and content: {(result.get('content') or '')[:50]}..."
            )

    logging.info(f"Deduplication: removed {len(results) - len(deduplicated)} duplicate entries from {len(results)} total")
    return deduplicated

def run_all_evaluations(valid_dirs: list[str] = None,
                        invalid_dirs: list[str] = None,
                        output_json: str = None,
                        output_summary_csv: str = None,
                        not_check_all_dirs: list[str] = None,
                        num_workers: int = None,
                        progress_label: str | None = None,
                        progress_stream: TextIO | None = None,
                        ):
    # Use CONFIG values as defaults
    valid_dirs = valid_dirs or CONFIG.get("valid_dirs", [])
    invalid_dirs = invalid_dirs or CONFIG.get("invalid_dirs", [])
    output_json = output_json or CONFIG.get("output_results_path", "evaluation_results/evaluation_results.json")
    output_summary_csv = output_summary_csv or CONFIG.get("output_summary_path", "evaluation_results/summary.csv")
    not_check_all_dirs = not_check_all_dirs or CONFIG.get("not_check_all_dirs", [])
    num_workers = num_workers or CONFIG.get("num_workers", 1)
    
    # Define output paths for additional files
    output_dir = os.path.dirname(output_json) or "."
    automata_csv_path = os.path.join(output_dir, "automata_sizes.csv")
    performance_csv_path = os.path.join(output_dir, "length_time_pairs.csv")
    runtime_error_log_path = os.path.join(output_dir, RUNTIME_ERROR_LOG_FILENAME)
    
    # Clear the parsing error log file before starting
    parsing_error_log_path = CONFIG.get("parsing_error_log_path")
    if parsing_error_log_path:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(parsing_error_log_path) or ".", exist_ok=True)
        # Clear or create the log file
        with open(parsing_error_log_path, 'w') as f:
            f.write("")
        logging.info(f"Cleared parsing error log at {parsing_error_log_path}")
    
    pipelines: list[tuple[str, bool]] = []
    start_time_total = time.time()
    
    valid_pipelines = find_scripts(valid_dirs)
    invalid_pipelines = find_scripts(invalid_dirs)
    pipelines.extend(zip(valid_pipelines, [True] * len(valid_pipelines)))
    pipelines.extend(zip(invalid_pipelines, [False] * len(invalid_pipelines)))
    
    if not pipelines:
        logging.error("No pipelines found")
        return

    progress = None
    progress_unique_keys: dict[str, set[tuple[str, str]]] = {}
    progress_seen_keys: dict[str, set[tuple[str, str]]] = {}
    if progress_label and progress_stream is not None:
        progress_unique_keys = unique_program_keys_by_category(pipelines, not_check_all_dirs)
        progress_seen_keys = {category: set() for category in progress_unique_keys}
        progress = CategoryProgress(
            progress_label,
            benchmark_program_totals_for(pipelines),
            progress_stream,
            unit="program",
        )

    results = []
    work_pipelines = group_pipelines_by_category(pipelines) if progress is not None else pipelines
    if num_workers > 1:
        if progress is not None:
            logging.warning("Per-category progress is only shown in sequential evaluation mode")
        logging.info(f"Running in parallel mode with {num_workers} workers")
        with multiprocessing.Pool(processes=num_workers) as pool:
            worker_func = partial(process_pipeline, not_check_all_dirs=not_check_all_dirs)
            result_lists = pool.map(worker_func, work_pipelines)
        results = [r for sublist in result_lists for r in sublist]
    else:
        logging.info("Running in sequential mode")
        for address, label in work_pipelines:
            check_all_pipelines = True
            if not check_all_pipelines_for_address(address, not_check_all_dirs):
                check_all_pipelines = False
            for pipeline_result in evaluate_pipeline_content(address, check_all_pipelines, label):
                add_result_metadata(pipeline_result, label)
                results.append(pipeline_result)
                if progress is not None:
                    category = infer_benchmark_name(address)
                    pipeline_content = pipeline_result.get("content")
                    progress_key = (normalize_result_path(address), pipeline_content)
                    if progress_key in progress_unique_keys.get(category, set()):
                        seen_keys = progress_seen_keys.setdefault(category, set())
                        if progress_key not in seen_keys:
                            seen_keys.add(progress_key)
                            progress.advance(category)
    if progress is not None:
        progress.finish()
        results = restore_result_order(results, pipelines)

    # Use functional approach for all statistics calculations
    unlabeled_inconsistent_results = [r for r in results if is_incorrect_prediction(r) and not has_result_category(r)]
    labeled_inconsistent_results = [r for r in results if is_incorrect_prediction(r) and has_result_category(r)]
    
    false_positive_pipelines = [r for r in results if is_false_positive(r)]
    false_negative_pipelines = [r for r in results if is_false_negative(r)]
    timeout_pipelines = [r for r in results if is_timeout(r)]
    valid_pipeline_crashes = [r for r in results if is_valid_pipeline_crash(r)]
    buggy_pipeline_crashes = [r for r in results if is_buggy_pipeline_crash(r)]
    
    # Count tainted pipelines
    untainted_pipelines = [r for r in results if is_untainted(r)]

    total_false_positives = len(false_positive_pipelines)
    total_false_negatives = len(false_negative_pipelines)
    total_correct_pipeline_crashes = len(valid_pipeline_crashes)
    total_buggy_pipeline_crashes = len(buggy_pipeline_crashes)
    total_timeouts = len(timeout_pipelines)
    total_correct_pipelines = len([r for r in results if is_valid_pipeline(r)])
    total_buggy_pipelines = len([r for r in results if is_buggy_pipeline(r)])
    
    # Calculate metrics using functional approach
    statistics = {
        "accuracy": calculate_accuracy_functional(results),
        "precision": calculate_precision_functional(results),
        "recall": calculate_recall_functional(results),
    }

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
    }
    
    # Add parser failures as no-warning benchmark rows, then deduplicate by
    # exact source address and pipeline content before writing summaries.
    results, output_data["statistics"] = add_parsing_failures_to_results(results, output_data["statistics"])
    results = deduplicate_results(results)
    
    # Use functional approach for all statistics after deduplication
    unlabeled_inconsistent_results = [r for r in results if is_incorrect_prediction(r) and not has_result_category(r)]
    labeled_inconsistent_results = [r for r in results if is_incorrect_prediction(r) and has_result_category(r)]
    false_positive_pipelines = [r for r in results if is_false_positive(r)]
    false_negative_pipelines = [r for r in results if is_false_negative(r)]
    timeout_pipelines = [r for r in results if is_timeout(r)]
    valid_pipeline_crashes = [r for r in results if is_valid_pipeline_crash(r)]
    buggy_pipeline_crashes = [r for r in results if is_buggy_pipeline_crash(r)]
    
    # Update statistics in output_data
    output_data["unlabeled_inconsistent_results"] = unlabeled_inconsistent_results
    output_data["labeled_inconsistent_results"] = labeled_inconsistent_results
    output_data["evaluation_results"] = results
    output_data["statistics"]["accuracy"] = calculate_accuracy_functional(results)
    output_data["statistics"]["precision"] = calculate_precision_functional(results)
    output_data["statistics"]["recall"] = calculate_recall_functional(results)
    output_data["statistics"]["total_pipelines"] = len(results)
    output_data["statistics"]["timeout_count"] = len(timeout_pipelines)
    output_data["statistics"]["crashes"] = len(valid_pipeline_crashes) + len(buggy_pipeline_crashes)
    output_data["statistics"]["correct_crashes"] = len(valid_pipeline_crashes)
    output_data["statistics"]["buggy_crashes"] = len(buggy_pipeline_crashes)
    output_data["statistics"]["total_correct_pipelines"] = len([r for r in results if is_valid_pipeline(r)])
    output_data["statistics"]["false_positives"] = len(false_positive_pipelines)
    output_data["statistics"]["false_positive_categories"] = categorize(false_positive_pipelines)
    output_data["statistics"]["total_buggy_pipelines"] = len([r for r in results if is_buggy_pipeline(r)])
    output_data["statistics"]["false_negatives"] = len(false_negative_pipelines)
    output_data["statistics"]["false_negative_categories"] = categorize(false_negative_pipelines)
    output_data["statistics"]["total_wrong_predictions"] = len(false_positive_pipelines) + len(false_negative_pipelines)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    write_runtime_errors_to_file(results, runtime_error_log_path)
    
    # Update output_data with filtered results for main JSON
    main_output_data = output_data.copy()
    main_output_data["evaluation_results"] = results
    
    # Write main results JSON
    with open(output_json, 'w') as json_file:
        json.dump(main_output_data, json_file, indent=4)
    logging.info(f"Results written to {output_json}")
    
    # Write summary CSV
    with open(output_summary_csv, 'w') as csv:
        tabulate(output_data['statistics'], csv)
    logging.info(f"Summary table written to {output_summary_csv}; format with `column -s, -t {output_summary_csv}`")
    
    # Write automata sizes CSV
    write_automata_sizes_to_csv(results, automata_csv_path)
    
    # Write performance data CSVs
    write_performance_data_to_csv(results, performance_csv_path)
    
    # Output function timer statistics
    try:
        from stream.utils.function_timer import FunctionTimerRegistry
        logging.info("Function execution statistics:")
        from io import StringIO
        timer_output = StringIO()
        with contextlib.redirect_stdout(timer_output):
            FunctionTimerRegistry.print_stats()
        logging.info(timer_output.getvalue())
    except ImportError:
        logging.warning("Function timer module not available - no timing statistics will be reported")
    
    logging.info(f"Total evaluation time: {total_time:.2f}s")

def categorize(results, category_label=CATEGORY_LABEL):
    categories = {}
    for r in results:
        if r[category_label] in categories:
            categories[r[category_label]] += 1
        else:
            categories[r[category_label]]  = 1
    return categories

def tabulate(result_stats, f):
    s = result_stats
    f.write("label,total,crash,signaled,false (pos/neg)\n")
    f.write("========,=====,=====,========,===============\n")
    f.write(f"correct,{s['total_correct_pipelines']},{s['correct_crashes']},{s['false_positives']},{s['false_positives']}\n")
    f.write("--------,-----,-----,--------,---------------\n")
    buggy_signals = s['total_buggy_pipelines'] - s['false_negatives'] - s['buggy_crashes']
    f.write(f"buggy,{s['total_buggy_pipelines']},{s['buggy_crashes']},{buggy_signals},{s['false_negatives']}\n")
    f.write("========,=====,=====,========,===============\n")
    f.write(f"total,{s['total_pipelines']},{s['crashes']}, ,{s['false_positives'] + s['false_negatives']}\n")

def write_automata_sizes_to_csv(results, csv_path):
    """Extract automata sizes from evaluation results and write to CSV"""
    automata_sizes = []
    
    for result in results:
        automata_size = result.get('automata_size')
        if automata_size is not None:
            automata_sizes.append(automata_size)
    
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['automata_size'])
        for size in automata_sizes:
            if size > 0 : 
                writer.writerow([size])
    
    logging.info(f"Automata sizes written to {csv_path}")

def write_performance_data_to_csv(results, csv_path):
    """Extract pipeline length and evaluation time data and write to CSV files"""
    length_time_pairs = []
    length_time_content_pairs = []
    
    for result in results:
        try:
            # Get evaluation time (remove the 's' suffix and convert to float)
            eval_time_str = result.get('evaluation_time', "0s")
            if eval_time_str.endswith('s'):
                eval_time = float(eval_time_str[:-1])
            else:
                eval_time = float(eval_time_str)
            
            # Get pipeline length
            pipeline_length = result.get('pipeline_length', 0)
            content = result.get('content', '')
            
            # Only include valid entries
            if pipeline_length > 0:
                length_time_pairs.append((pipeline_length, eval_time))
                if content:
                    length_time_content_pairs.append((pipeline_length, eval_time, content))
        except Exception as e:
            logging.error(f"Error processing performance data: {e}")
    
    # Write main performance CSV
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Length', 'Time'])  # Header
        for length, time_val in length_time_pairs:
            writer.writerow([length, time_val])
    
    # Write extended CSV with content
    content_csv_path = os.path.splitext(csv_path)[0] + "_with_content.csv"
    with open(content_csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Length', 'Time', 'Content'])  # Header
        for length, time_val, content in length_time_content_pairs:
            writer.writerow([length, time_val, content])
    
    logging.info(f"Performance data written to {csv_path}")
    logging.info(f"Performance data with content written to {content_csv_path}")

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
    parser.add_argument('--disable_rule_no_meaningless_command', action='store_true',
                        help='Disable the rule that checks for meaningless commands.')
    parser.add_argument('--disable_rule_no_sort_non_numeric_with_numeric_input', action='store_true',
                        help='Disable the rule that checks for numeric sorting of non-numeric data.')

    parser.add_argument('--disable_fsts', action='store_true',
                        help='Disable FSTs. Defaults to enabled.')
    parser.add_argument('--disable_concretization', action='store_true',
                        help='Disable concretize annotations while leaving other annotations enabled.')
    parser.add_argument('--outdir', default=None, type=str,
                        help='Output directory, to override whatever is in the global_config.yaml (but using the same file names)')
    parser.add_argument('--progress', action='store_true',
                        help='Show per-category progress on stdout.')
    parser.add_argument('--progress-label', default=None, type=str,
                        help='Label to display before each progress bar.')
    parser.add_argument('--log-file', default=None, type=str,
                        help='Write evaluation logs and stray output to this file.')

    args = parser.parse_args()

    # Override CONFIG with command line args
    if args.disable_annotation:
        enable_user_annotation = False
        CONFIG["enable_user_annotation"] = False
    else:
        enable_user_annotation = CONFIG.get("enable_user_annotation", True)

    if args.disable_fsts:
        CONFIG["enable_FST"] = False

    if args.disable_concretization:
        CONFIG["enable_concretization"] = False

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

    if args.disable_rule_no_empty_output:
        CONFIG["enable_rule_no_empty_output"] = False
    if args.disable_rule_no_ignored_input:
        CONFIG["enable_rule_no_ignored_input"] = False
    if args.disable_rule_no_meaningless_command:
        CONFIG["enable_rule_no_meaningless_command"] = False
    if args.disable_rule_no_sort_non_numeric_with_numeric_input:
        CONFIG["enable_rule_no_sort_non_numeric_with_numeric_input"] = False
        
    log_handlers = []
    if args.log_file:
        os.makedirs(os.path.dirname(args.log_file) or ".", exist_ok=True)
        log_handlers.append(logging.FileHandler(args.log_file, mode="a", encoding="utf-8"))
    else:
        log_handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=level,
        handlers=log_handlers,
        format="%(levelname)s:%(name)s:%(message)s",
        force=True,
    )
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
    logging.info(f"Concretization annotations: {CONFIG.get('enable_concretization', True)}")

    logging.getLogger().setLevel(level)

    time.sleep(3)

    # Set up output paths based on outdir parameter
    output_dir = args.outdir if args.outdir else None
    
    if output_dir:
        # Create proper path for all output files
        result_filename = os.path.basename(CONFIG.get("output_results_path_with_annotation" if enable_user_annotation else "output_results_path_raw"))
        summary_filename = os.path.basename(CONFIG.get("output_summary_path_with_annotation" if enable_user_annotation else "output_summary_path_raw"))
        
        output_json = os.path.join(output_dir, result_filename)
        output_summary_csv = os.path.join(output_dir, summary_filename)
    else:
        # Use default paths from CONFIG
        output_json = CONFIG.get("output_results_path_with_annotation" if enable_user_annotation else "output_results_path_raw")
        output_summary_csv = CONFIG.get("output_summary_path_with_annotation" if enable_user_annotation else "output_summary_path_raw")
    
    original_stdout = sys.stdout
    progress_label = args.progress_label or "RT"

    try:
        if args.progress and args.log_file:
            with redirect_process_output_to_log(args.log_file) as progress_stream:
                run_all_evaluations(
                    num_workers=workers,
                    output_json=output_json,
                    output_summary_csv=output_summary_csv,
                    progress_label=progress_label,
                    progress_stream=progress_stream,
                )
        else:
            run_all_evaluations(
                num_workers=workers,
                output_json=output_json,
                output_summary_csv=output_summary_csv,
                progress_label=progress_label if args.progress else None,
                progress_stream=original_stdout if args.progress else None,
            )
        Timing.finish_all()
    except Exception:
        if args.log_file:
            logging.exception("Evaluation failed")
            sys.exit(1)
        raise
