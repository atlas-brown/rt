import os
import json
import logging
from typing import Optional
from stream.type_checker import TypeChecker

class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_entries = []

    def emit(self, record):
        log_entry = self.format(record)
        self.log_entries.append(log_entry)

list_handler = ListHandler()
logging.basicConfig(level=logging.INFO, handlers=[list_handler, logging.StreamHandler()])
logger = logging.getLogger()

def evaluate_pipeline(pipeline_address) -> dict:
    pipeline_data = {
        "path": pipeline_address,
        "ground_truth": None,
        "prediction": None,
        "error message generated": None,
        "tool runtime error": None,
        "content": None,
        "notes": ""
    }
    try:
        with open(pipeline_address, 'r') as file:
            pipeline_data["content"] = file.read()

        type_checker = TypeChecker(pipeline_address)
        result, err_msg = type_checker.check_pipeline()
        
        pipeline_data["prediction"] = result
        logging.info(f'Pipeline {pipeline_address} evaluated as {result}')
        
        if not result:
            pipeline_data["error message generated"] = err_msg
            logging.info(f'Error detected in pipeline {pipeline_address}: {err_msg}')
    except Exception as e:
        logging.error(f'Tool runtime error while evaluating pipeline {pipeline_address}: {e}')
        pipeline_data["tool runtime error"] = str(e)
    
    return pipeline_data

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

def run_all_evaluations(output_json='evaluation_results/evaluation_results.json'):
    valid_pipelines = ['./evaluation_pipelines/valid/' + pipeline for pipeline in os.listdir('./evaluation_pipelines/valid')]
    invalid_pipelines = ['./evaluation_pipelines/invalid/' + pipeline for pipeline in os.listdir('./evaluation_pipelines/invalid')]

    pipelines = valid_pipelines + invalid_pipelines
    labels = [True] * len(valid_pipelines) + [False] * len(invalid_pipelines)
    results = []

    correct_valid_count = 0
    correct_invalid_count = 0

    for pipeline, label in zip(pipelines, labels):
        pipeline_result = evaluate_pipeline(pipeline)
        pipeline_result["ground_truth"] = label
        results.append(pipeline_result)
        
        if pipeline_result["prediction"] == label:
            if label:
                correct_valid_count += 1
            else:
                correct_invalid_count += 1

    preds = [result["prediction"] for result in results]
    accuracy = calculate_accuracy(labels, preds)
    precision = calculate_precision(labels, preds)
    recall = calculate_recall(labels, preds)
    fail_rate = calculate_fail_rate(labels, preds)

    logging.info(f'Accuracy: {accuracy}')
    logging.info(f'Precision: {precision}')
    logging.info(f'Recall: {recall}')
    logging.info(f'Fail rate: {fail_rate}')
    logging.info(f'Total correct valid pipelines: {correct_valid_count}')
    logging.info(f'Total buggy pipelines detected: {correct_invalid_count}')

    output_data = {
        "evaluation_results": results,
        "statistics": {
            "correct_valid_pipelines": correct_valid_count,
            "correct_pipelines_handled": f"{correct_valid_count}/{len(valid_pipelines)}",
            "buggy_pipelines_detected": f"{correct_invalid_count}/{len(invalid_pipelines)}",
            "wrong_predictions": sum(1 for label, pred in zip(labels, preds) if label != pred and pred is not None),
            "failed_predictions": sum(1 for _, pred in zip(labels, preds) if pred is None),
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "fail_rate": fail_rate
        },
        "logs": list_handler.log_entries
    }

    with open(output_json, 'w') as json_file:
        json.dump(output_data, json_file, indent=4)
    logging.info(f"Results written to {output_json}")

if __name__ == "__main__":
    run_all_evaluations()
