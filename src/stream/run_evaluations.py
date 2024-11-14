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

pipeline_pattern = re.compile(r'(\bgrep\b|\bawk\b|\bsed\b|\bcut\b|\bsort\b|\buniq\b|\btr\b|\bxargs\b|\becho\b|\bcat\b).*\|\s*')
temp_pipeline_address = './temp.sh'
TIMEOUT_SECONDS = 2

IS_BUGGY_LABEL="is buggy?"
SIGNALED_LABEL="warning signaled?"
PIPELINE_ID_LABEL="id"
CATEGORY_LABEL="category"
CRASH_REASON_LABEL="tool runtime error"
TIMEOUT_REASON="Timeout"

# PipelineID := (path-string, natural)

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Evaluation timed out")

def with_timeout(seconds):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result_queue = multiprocessing.Queue()
            
            def worker(queue):
                try:
                    os.setpgrp()
                    result = func(*args, **kwargs)
                    queue.put(result)
                except Exception as e:
                    queue.put(e)

            process = multiprocessing.Process(target=worker, args=(result_queue,))
            process.start()
            
            try:
                result = result_queue.get(timeout=seconds)
                
                if isinstance(result, Exception):
                    raise result
                    
                return result
            except Empty:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except:
                    pass
                raise TimeoutError(f"Function timed out after {seconds} seconds")
            finally:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=0.1)
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except:
                        pass
                while not result_queue.empty():
                    try:
                        result_queue.get_nowait()
                    except:
                        pass

        return wrapper
    return decorator

class LogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_entries = []

    def emit(self, record):
        log_entry = self.format(record)
        self.log_entries.append(log_entry)

log_handler = LogHandler()
logging.basicConfig(level=logging.INFO, handlers=[log_handler, logging.StreamHandler()])
logger = logging.getLogger()

# # TODO: parse pipelines properly using shasta & libdash!
# def extract_pipelines_in_json(obj, pipelines=None):
#     if pipelines is None:
#         pipelines = []
    
#     if isinstance(obj, dict):
#         for value in obj.values():
#             if isinstance(value, str):
#                 value = value.strip()
#                 if pipeline_pattern.search(value) and not value.strip().startswith('#'):
#                     pipelines.append(value.strip())
#             else:
#                 extract_pipelines_in_json(value, pipelines)
#     elif isinstance(obj, list):
#         for item in obj:
#             extract_pipelines_in_json(item, pipelines)
#     return pipelines

# def extract_pipelines_from_file(file_path: str) -> list[str]:
#     file_ext = os.path.splitext(file_path)[1].lower()
    
#     if file_ext == '.json':
#         with open(file_path, 'r') as f:
#             data = json.load(f)
#             pipelines = extract_pipelines_in_json(data)
#             return pipelines if pipelines else []
    
#     elif file_ext == '.sh':
#         with open(file_path, encoding="utf8", errors='ignore') as f:
#             content = f.read()
#             pipelines = []
#             for line in content.split('\n'):
#                 line = line.strip()
#                 if pipeline_pattern.search(line) and not line.startswith('#'):
#                     pipelines.append(line)
#             return pipelines if pipelines else []
#     return []

# listof(directory-path) bool -> listof((PipelineID, bool, str))
#                          is_valid == not is_buggy? ^     ^ pipeline content
def find_pipelines(directories: list[str], is_valid: bool) -> List[Tuple[str, bool, str]]:
    all_pipelines = []
    
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.sh')):
                    file_path = os.path.join(root, file)
                    pipelines = extract_pipelines_from_file(file_path)
                    if pipelines:
                        i = 0
                        for pipeline in pipelines:
                            all_pipelines.append(((file_path, i), is_valid, pipeline))
                            i += 1
    
    return all_pipelines

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

def calculate_fail_rate(labels, preds):
    fail_count = sum(1 for _, pred in zip(labels, preds) if pred is None)
    logging.info(f'Failed predictions: {fail_count}')
    return fail_count / len(labels)

@with_timeout(TIMEOUT_SECONDS)
def evaluate_pipeline_with_timeout(type_checker: TypeChecker) -> list[CheckingResult]:
    return type_checker.check_pipeline()

def evaluate_pipeline_content(pipeline: str, ID: 'PipelineID') -> dict:
    pipeline_data = {
        PIPELINE_ID_LABEL: ID,
        IS_BUGGY_LABEL: None,
        SIGNALED_LABEL: None,
        "error message generated": None,
        CRASH_REASON_LABEL: None,
        "content": pipeline,
        "evaluation_time": None,
        "notes": ""
    }
    
    try:
        # TODO: why doesn't typechecker accept parsed pipeline?
        with open(temp_pipeline_address, 'w') as f:
            f.write(pipeline)
        
        start_time = time.time()
        type_checker = TypeChecker(temp_pipeline_address)
        
        try:
            checking_results = evaluate_pipeline_with_timeout(type_checker)
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            pipeline_data["evaluation_time"] = elapsed_time
            pipeline_data[SIGNALED_LABEL] = result
            logging.info(f'Pipeline from {ID} evaluated as {result} in {elapsed_time:.2f}s')
            
            if not result:
                pipeline_data["error message generated"] = err_msg
                logging.info(f'Error detected in pipeline from {ID}: {err_msg}')
                
        except TimeoutError:
            pipeline_data["notes"] = f"Evaluation timeout after {TIMEOUT_SECONDS}s"
            pipeline_data[CRASH_REASON_LABEL] = TIMEOUT_REASON
            logging.warning(f'Pipeline evaluation timed out for {ID}')
            
    except Exception as e:
        logging.error(f'Tool runtime error while evaluating pipeline from {ID}: {e}')
        pipeline_data[CRASH_REASON_LABEL] = str(e)
    
    return pipeline_data

def run_all_evaluations(valid_dirs: list[str],
                        invalid_dirs: list[str],
                        output_json='evaluation_results/evaluation_results.json',
                        output_summary_csv='evaluation_results/summary.csv',
                        evaluation_notes_json='src/stream/evaluation_notes.json'):
    try:
        with open(evaluation_notes_json, 'r') as f:
            evaluation_notes = json.load(f)

        pipelines = []
        start_time_total = time.time()
        
        valid_pipelines = find_pipelines(valid_dirs, True)
        invalid_pipelines = find_pipelines(invalid_dirs, False)
        total_correct_pipelines = len(valid_pipelines)
        total_buggy_pipelines = len(invalid_pipelines)

        pipelines.extend(valid_pipelines)
        pipelines.extend(invalid_pipelines)
        
        if not pipelines:
            logging.error("No pipelines found")
            return

        results = []

        for ID, label, pipeline in pipelines:
            notes = notes_lookup(evaluation_notes, ID) or {CATEGORY_LABEL: "<missing>", "notes": ""}
            pipeline_result = evaluate_pipeline_content(pipeline, ID)
            pipeline_result[IS_BUGGY_LABEL] = not label
            pipeline_result[CATEGORY_LABEL] = notes[CATEGORY_LABEL]
            pipeline_result["notes"] = notes["notes"]
            results.append(pipeline_result)

        failures = [result for result in results if result[IS_BUGGY_LABEL] != result[SIGNALED_LABEL]]
        crash_pipelines = [r for r in failures if r[SIGNALED_LABEL] == None]
        timeout_pipelines =      [r for r in crash_pipelines if r[CRASH_REASON_LABEL] == TIMEOUT_REASON]
        valid_pipeline_crashes = [r for r in crash_pipelines if not r[IS_BUGGY_LABEL] and r[CRASH_REASON_LABEL] != None]
        buggy_pipeline_crashes = [r for r in crash_pipelines if     r[IS_BUGGY_LABEL] and r[CRASH_REASON_LABEL] != None]
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
                "fail_rate": calculate_fail_rate(labels, preds)
            })

            logging.info(f'Accuracy: {statistics["accuracy"]}')
            logging.info(f'Precision: {statistics["precision"]}')
            logging.info(f'Recall: {statistics["recall"]}')
            logging.info(f'Fail rate: {statistics["fail_rate"]}')
            logging.info(f'Total correct valid pipelines: {total_correct_pipelines - total_false_positives - total_correct_pipeline_crashes}')
            logging.info(f'Total buggy pipelines detected: {total_buggy_pipelines - total_false_negatives - total_buggy_pipeline_crashes}')
            logging.info(f'Total timeouts: {total_timeouts}')

        end_time_total = time.time()
        total_time = end_time_total - start_time_total

        output_data = {
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
            "logs": log_handler.log_entries
        }

        os.makedirs(os.path.dirname(output_json), exist_ok=True)
        with open(output_json, 'w') as json_file:
            json.dump(output_data, json_file, indent=4)
        logging.info(f"Results written to {output_json}")
        with open(output_summary_csv, 'w') as csv:
            tabulate(output_data['statistics'], csv)
        logging.info(f"Summary table written to {output_summary_csv}; format with `column -s, -t {output_summary_csv}`")
        logging.info(f"Total evaluation time: {total_time:.2f}s")
        
    finally:
        if os.path.exists(temp_pipeline_address):
            os.remove(temp_pipeline_address)

def categorize(results):
    categories = {}
    for r in results:
        if r[CATEGORY_LABEL] in categories:
            categories[r[CATEGORY_LABEL]] += 1
        else:
            categories[r[CATEGORY_LABEL]]  = 1
    return categories

# TODO: might be nice to put this in a separate module to tabulate already-existing results
def tabulate(result_stats, f):
    s = result_stats
    f.write("category,total,crash,signaled,false (pos/neg),category\n")
    f.write("========,=====,=====,========,===============,========\n")
    f.write(f"correct,{s['total_correct_pipelines']},{s['correct_crashes']},{s['false_positives']},{s['false_positives']}, \n")
    for category, count in s['false_positive_categories'].items():
        f.write(f" , , , ,{count},{category}\n")
    f.write("--------,-----,-----,--------,---------------,--------\n")
    buggy_signals = s['total_buggy_pipelines'] - s['false_negatives'] - s['buggy_crashes']
    f.write(f"buggy,{s['total_buggy_pipelines']},{s['buggy_crashes']},{buggy_signals},{s['false_negatives']}, \n")
    for category, count in s['false_negative_categories'].items():
        f.write(f" , , , ,{count},{category}\n")
    f.write("========,=====,=====,========,===============,========\n")
    f.write(f"total,{s['total_pipelines']},{s['crashes']}, ,{s['false_positives'] + s['false_negatives']}, \n")

# listof(Note) PipelineID -> Optional(Note)
def notes_lookup(notes, pipeline_id):
    ID = list(pipeline_id)
    for note in notes:
        if note["pipeline_id"] == ID:
            return note
    return None

if __name__ == "__main__":
    run_all_evaluations(
        valid_dirs=[
                    "./evaluation_pipelines/valid", 
                    "./full_benchmark/intercode/InterCode-ALFA-Data", 
                    # "./full_benchmark/Shseer",
                    "./full_benchmark/pash_benchmark/benchmarks/unix50"
        ],
        invalid_dirs=["./evaluation_pipelines/invalid"]
    )
