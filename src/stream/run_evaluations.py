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
from stream.type_checker import TypeChecker

pipeline_pattern = re.compile(r'(\bgrep\b|\bawk\b|\bsed\b|\bcut\b|\bsort\b|\buniq\b|\btr\b|\bxargs\b|\becho\b|\bcat\b).*\|\s*')
temp_pipeline_address = './temp.sh'
TIMEOUT_SECONDS = 2

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

def extract_pipelines_in_json(obj, pipelines=None):
    if pipelines is None:
        pipelines = []
    
    if isinstance(obj, dict):
        for value in obj.values():
            if isinstance(value, str):
                value = value.strip()
                if pipeline_pattern.search(value) and not value.strip().startswith('#'):
                    pipelines.append(value.strip())
            else:
                extract_pipelines_in_json(value, pipelines)
    elif isinstance(obj, list):
        for item in obj:
            extract_pipelines_in_json(item, pipelines)
    return pipelines

def extract_pipelines_from_file(file_path: str) -> list[str]:
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.json':
        with open(file_path, 'r') as f:
            data = json.load(f)
            pipelines = extract_pipelines_in_json(data)
            return pipelines if pipelines else []
    
    elif file_ext == '.sh':
        with open(file_path, encoding="utf8", errors='ignore') as f:
            content = f.read()
            pipelines = []
            for line in content.split('\n'):
                line = line.strip()
                if pipeline_pattern.search(line) and not line.startswith('#'):
                    pipelines.append(line)
            return pipelines if pipelines else []
    return []

def find_pipeline_files(directories: list[str], is_valid: bool) -> List[Tuple[str, bool, str]]:
    pipeline_files = []
    
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.json', '.sh')):
                    file_path = os.path.join(root, file)
                    pipelines = extract_pipelines_from_file(file_path)
                    if pipelines:
                        for pipeline in pipelines:
                            pipeline_files.append((file_path, is_valid, pipeline))
    
    return pipeline_files

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
def evaluate_pipeline_with_timeout(type_checker: TypeChecker) -> Tuple[bool, str]:
    return type_checker.check_pipeline()

def evaluate_pipeline_content(pipeline: str, original_path: str) -> dict:
    pipeline_data = {
        "path": original_path,
        "ground_truth": None,
        "prediction": None,
        "error message generated": None,
        "tool runtime error": None,
        "content": pipeline,
        "evaluation_time": None,
        "notes": "",
    }
    
    try:
        with open(temp_pipeline_address, 'w') as f:
            f.write(pipeline)
        
        start_time = time.time()
        type_checker = TypeChecker(temp_pipeline_address)
        
        try:
            result, err_msg = evaluate_pipeline_with_timeout(type_checker)
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            pipeline_data["evaluation_time"] = elapsed_time
            pipeline_data["prediction"] = result
            logging.info(f'Pipeline from {original_path} evaluated as {result} in {elapsed_time:.2f}s')
            
            if not result:
                pipeline_data["error message generated"] = err_msg
                logging.info(f'Error detected in pipeline from {original_path}: {err_msg}')
                
        except TimeoutError:
            pipeline_data["notes"] = f"Evaluation timeout after {TIMEOUT_SECONDS}s"
            pipeline_data["tool runtime error"] = "Timeout"
            pipeline_data["prediction"] = None
            logging.warning(f'Pipeline evaluation timed out for {original_path}')
            
    except Exception as e:
        logging.error(f'Tool runtime error while evaluating pipeline from {original_path}: {e}')
        pipeline_data["tool runtime error"] = str(e)
    
    return pipeline_data

def run_all_evaluations(valid_dirs: list[str], invalid_dirs: list[str], output_json='evaluation_results/evaluation_results.json'):
    try:
        pipeline_files = []
        start_time_total = time.time()
        
        pipeline_files.extend(find_pipeline_files(valid_dirs, True))
        pipeline_files.extend(find_pipeline_files(invalid_dirs, False))
        
        if not pipeline_files:
            logging.error("No pipeline files found")
            return

        results = []
        correct_valid_count = 0
        correct_invalid_count = 0
        timeout_count = 0

        for file_path, label, pipeline in pipeline_files:
            pipeline_result = evaluate_pipeline_content(pipeline, file_path)
            pipeline_result["ground_truth"] = label
            results.append(pipeline_result)
            
            if pipeline_result["tool runtime error"] == "Timeout":
                timeout_count += 1
                continue
                
            if pipeline_result["prediction"] == label:
                if label:
                    correct_valid_count += 1
                else:
                    correct_invalid_count += 1

        preds = [result["prediction"] for result in results if result["tool runtime error"] != "Timeout"]
        labels = [result["ground_truth"] for result in results if result["tool runtime error"] != "Timeout"]
        
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
            logging.info(f'Total correct valid pipelines: {correct_valid_count}')
            logging.info(f'Total buggy pipelines detected: {correct_invalid_count}')
            logging.info(f'Total timeouts: {timeout_count}')

        end_time_total = time.time()
        total_time = end_time_total - start_time_total

        output_data = {
            "evaluation_results": results,
            "statistics": {
                **statistics,
                "total_evaluation_time": f"{total_time:.2f}s",
                "timeout_count": timeout_count,
                "correct_valid_pipelines": correct_valid_count,
                "correct_pipelines_handled": f"{correct_valid_count}/{sum(1 for label in labels if label)}",
                "buggy_pipelines_detected": f"{correct_invalid_count}/{sum(1 for label in labels if not label)}",
                "wrong_predictions": sum(1 for label, pred in zip(labels, preds) if label != pred and pred is not None),
                "failed_predictions": sum(1 for _, pred in zip(labels, preds) if pred is None),
            },
            "logs": log_handler.log_entries
        }

        os.makedirs(os.path.dirname(output_json), exist_ok=True)
        with open(output_json, 'w') as json_file:
            json.dump(output_data, json_file, indent=4)
        logging.info(f"Results written to {output_json}")
        logging.info(f"Total evaluation time: {total_time:.2f}s")
        
    finally:
        if os.path.exists(temp_pipeline_address):
            os.remove(temp_pipeline_address)

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