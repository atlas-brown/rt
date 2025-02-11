import multiprocessing
import os
import json
import logging
from queue import Empty
import re
import time
import signal
from functools import wraps
from typing import Optional, List, Tuple
from stream.checking_result import CheckingResult
from stream.type_checker import TypeChecker
from stream.tool_error import PashAnnotationParsingError, TimeoutError
import argparse

ENABLE_TIMEOUT = False
TIMEOUT_SECONDS = 10

IS_BUGGY_LABEL="is buggy?"
SIGNALED_LABEL="warning signaled?"
PIPELINE_ID_LABEL="id"
CATEGORY_LABEL="category"
CRASH_REASON_LABEL="tool runtime error"
TIMEOUT_REASON=f"Timeout after {TIMEOUT_SECONDS}s"


enable_user_annotation = True

# class LogHandler(logging.Handler):
#     def __init__(self):
#         super().__init__()
#         self.log_entries = []

#     def emit(self, record):
#         log_entry = self.format(record)
#         self.log_entries.append(log_entry)

# log_handler = LogHandler()
# logging.basicConfig(level=logging.INFO, handlers=[log_handler, logging.StreamHandler()])
# logger = logging.getLogger()

def find_scripts(directories: list[str]) -> list[str]:
    script_addresses = []
    
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.sh')):
                    file_path = os.path.join(root, file)
                    script_addresses.append(file_path)
    
    return script_addresses

def calculate_accuracy(labels, preds):
    correct_count = sum(1 for label, pred in zip(labels, preds) if label == pred)
    logging.info(f'Correct predictions: {correct_count}')
    return correct_count / len(labels)

def calculate_precision(labels, preds):
    TP = sum(1 for label, pred in zip(labels, preds) if label == pred and not label)
    logging.info(f'TP (True Positives for buggy pipelines): {TP}')
    return TP / sum(1 for pred in preds if pred == False)

def calculate_recall(labels, preds):
    recall = sum(1 for label, pred in zip(labels, preds) if label == pred and not label) / sum(1 for label in labels if not label)
    logging.info(f'Recall: {recall}')
    return recall

def calculate_crash_rate(labels, preds):
    crash_count = sum(1 for _, pred in zip(labels, preds) if pred is None)
    logging.info(f'Crash: {crash_count}')
    return crash_count / len(labels)


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
        # "notes": ""
    }
    pipeline_data_list = []
    
    try:        
        type_checker = TypeChecker(address, enable_user_annotations=enable_user_annotation, enable_stage_timeout=ENABLE_TIMEOUT, stage_timeout=TIMEOUT_SECONDS, check_all_pipelines=check_all_pipelines)

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

def run_all_evaluations(valid_dirs: list[str],
                        invalid_dirs: list[str],
                        output_json='evaluation_results/evaluation_results.json',
                        output_summary_csv='evaluation_results/summary.csv',
                        evaluation_notes_json='src/stream/evaluation_notes.json',
                        not_check_all_dirs: list[str] = [],
                        ):
    with open(evaluation_notes_json, 'r') as f:
        evaluation_notes = json.load(f)

    pipelines: list[tuple[str, bool]] = []
    start_time_total = time.time()
    
    valid_pipelines = find_scripts(valid_dirs)
    invalid_pipelines = find_scripts(invalid_dirs)
    total_correct_pipelines = len(valid_pipelines)
    total_buggy_pipelines = len(invalid_pipelines)

    pipelines.extend(zip(valid_pipelines, [True] * len(valid_pipelines)))
    pipelines.extend(zip(invalid_pipelines, [False] * len(invalid_pipelines)))
    
    if not pipelines:
        logging.error("No pipelines found")
        return

    results = []

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

    total_false_positives = len(false_positive_pipelines)
    total_false_negatives = len(false_negative_pipelines)
    total_correct_pipeline_crashes = len(valid_pipeline_crashes)
    total_buggy_pipeline_crashes = len(buggy_pipeline_crashes)
    total_timeouts = len(timeout_pipelines)
    assert len(failures) == (total_correct_pipeline_crashes + total_buggy_pipeline_crashes + \
                                total_false_positives + total_false_negatives)

    preds = [result[SIGNALED_LABEL] for result in results if result[CRASH_REASON_LABEL] != TIMEOUT_REASON]
    labels = [result[IS_BUGGY_LABEL] for result in results if result[CRASH_REASON_LABEL] != TIMEOUT_REASON]
    
    statistics = {}
    if preds and labels:
        statistics.update({
            "accuracy": calculate_accuracy(labels, preds),
            "precision": calculate_precision(labels, preds),
            "recall": calculate_recall(labels, preds),
            "crash_rate": calculate_crash_rate(labels, preds)
        })

        logging.info(f'Accuracy: {statistics["accuracy"]}')
        logging.info(f'Precision: {statistics["precision"]}')
        logging.info(f'Recall: {statistics["recall"]}')
        logging.info(f'Crash rate: {statistics["crash_rate"]}')
        logging.info(f'Total correct valid pipelines: {total_correct_pipelines - total_false_positives - total_correct_pipeline_crashes}')
        logging.info(f'Total buggy pipelines detected: {total_buggy_pipelines - total_false_negatives - total_buggy_pipeline_crashes}')
        logging.info(f'Total timeouts: {total_timeouts}')

    end_time_total = time.time()
    total_time = end_time_total - start_time_total

    output_data = {
        "unlabeled_inconsistent_results": unlabeled_inconsistent_results,
        "labeled_inconsistent_results": labeled_inconsistent_results,
        "evaluation_results": results,
        "statistics": {
            **statistics,

            "total_pipelines": len(results),

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

            "total_evaluation_time": f"{total_time:.2f}s",
            "timeout_count": total_timeouts,
        },
        # "logs": log_handler.log_entries
    }

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
    f.write("========,=====,=====,========,===============,========\n")
    f.write(f"correct,{s['total_correct_pipelines']},{s['correct_crashes']},{s['false_positives']},{s['false_positives']}, \n")
    for category, count in s['false_positive_categories'].items():
        f.write(f" , , , ,{count},{category.replace(',', ';')},{category_to_tag(category)}\n")
    f.write("--------,-----,-----,--------,---------------,--------\n")
    buggy_signals = s['total_buggy_pipelines'] - s['false_negatives'] - s['buggy_crashes']
    f.write(f"buggy,{s['total_buggy_pipelines']},{s['buggy_crashes']},{buggy_signals},{s['false_negatives']}, \n")
    for category, count in s['false_negative_categories'].items():
        f.write(f" , , , ,{count},{category.replace(',', ';')},{category_to_tag(category)}\n")
    f.write("========,=====,=====,========,===============,========\n")
    f.write(f"total,{s['total_pipelines']},{s['crashes']}, ,{s['false_positives'] + s['false_negatives']}, \n")

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
    parser.add_argument('--user_annotation', default="true", type=str,
                        help='Enable user annotation handling. Defaults to True.')
    parser.add_argument('--log_level', default='info', type=str, help='Set logging level: info, debug, error. Defaults to info.')
    parser.add_argument('--timeout', default=-1, type=int,
                        help='Set pipeline evaluation timeout in seconds. Defaults to disabled.')

    args = parser.parse_args()

    user_annotation = args.user_annotation.lower()
    if user_annotation == "false":
        enable_user_annotation = False
    else:
        enable_user_annotation = True

    level_str = args.log_level.lower()
    if level_str == "debug":
        level = logging.DEBUG
    elif level_str == "error":
        level = logging.WARNING
    else:
        level = logging.INFO

    TIMEOUT_SECONDS = args.timeout
    if TIMEOUT_SECONDS > 0:
        ENABLE_TIMEOUT = True
        TIMEOUT_REASON=f"Timeout after {TIMEOUT_SECONDS}s"

    logging.basicConfig(level=logging.INFO)
    logging.info(f"Enable user annotation: {enable_user_annotation}")
    logging.info(f"Logging level: {level_str}")
    if ENABLE_TIMEOUT:
        logging.info(f"Timeout set to: {TIMEOUT_SECONDS} seconds")
    else:
        logging.info("Timeout disabled")

    logging.getLogger().setLevel(level)

    run_all_evaluations(
        valid_dirs=[
                    "./evaluation_pipelines/valid", 
                    "./full_benchmark/intercode/pipelines", 
                    # "./full_benchmark/Shseer/evaluation/tests/ShellExtractResults/",
                    # "./full_benchmark/pash_benchmark/benchmarks",
                    "./full_benchmark/pash_benchmark/benchmarks/unix50",
                    # "./full_benchmark/github_repos_commits/output/post_commit",
        ],
        invalid_dirs=[
                        "./evaluation_pipelines/invalid",
                      "./full_benchmark/curated_mutants",
                      "./full_benchmark/llm_injection/pipelines",
                    #   "./full_benchmark/github_repos_commits/output/pre_commit",
        ],
        not_check_all_dirs=[
            "./full_benchmark/github_repos_commits/output/post_commit",
            "./full_benchmark/github_repos_commits/output/pre_commit",
        ],
        output_json='evaluation_results/with_annotations/evaluation_results.json' if enable_user_annotation else 'evaluation_results/raw/evaluation_results.json',
        output_summary_csv='evaluation_results/with_annotations/summary.csv' if enable_user_annotation else 'evaluation_results/raw/summary.csv',

    )
