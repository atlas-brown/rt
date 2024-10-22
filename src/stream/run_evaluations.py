import os
import sys
from typing import Optional
from stream.shell_parser import parse_shell_to_asts
from stream.pipeline_parser import PipelineParser
from stream.regular_type import RegularType
from stream.type_checker import TypeChecker
import logging


def evaluate_pipeline(pipeline_address) -> Optional[bool]:
        try:
            type_checker = TypeChecker(pipeline_address)
            result = type_checker.check_pipeline()
            logging.info(f'Pipeline {pipeline_address} evaluated as {result}')
            return result
        except Exception as e:
            logging.error(f'Error while evaluating pipeline {pipeline_address}: {e}')
            return None

def calculate_accuracy(labels, preds):
    correct_count = sum(1 for label, pred in zip(labels, preds) if label == pred)
    logging.info(f'Correct predictions: {correct_count}')
    wrong_count = sum(1 for label, pred in zip(labels, preds) if label != pred and pred != None)
    failed_count = sum(1 for label, pred in zip(labels, preds) if pred == None)
    logging.info(f'Wrong predictions: {wrong_count}')
    logging.info(f'Failed predictions: {failed_count}')
    return correct_count / len(labels)

def calculate_precision(labels, preds):
    TP = sum(1 for label, pred in zip(labels, preds) if label == pred and label == True)
    logging.info(f'TP: {TP}')
    return TP / sum(1 for pred in preds if pred == True)

def calculate_recall(labels, preds):
    return sum(1 for label, pred in zip(labels, preds) if label == pred and label == True) / sum(1 for label in labels if label == True)

def calculate_fail_rate(labels, preds):
    count = sum(1 for _, pred in zip(labels, preds) if pred == None)
    logging.info(f'Failed predictions: {count}')
    return count / len(labels)

def run_all_evaluations():

    valid_pipelines = ['./evaluation_pipelines/valid/' + pipeline for pipeline in os.listdir('./evaluation_pipelines/valid')]
    print(valid_pipelines)
    invalid_pipelines = ['./evaluation_pipelines/invalid/' + pipeline for pipeline in os.listdir('./evaluation_pipelines/invalid')]
    logging.info(f'Found {len(valid_pipelines)} valid pipelines and {len(invalid_pipelines)} invalid pipelines.')

    labels = [True] * len(valid_pipelines) + [False] * len(invalid_pipelines)
    preds = []

    for pipeline in valid_pipelines + invalid_pipelines:
        preds.append(evaluate_pipeline(pipeline))

    accuracy = calculate_accuracy(labels, preds)
    precision = calculate_precision(labels, preds)
    recall = calculate_recall(labels, preds)
    fail_rate = calculate_fail_rate(labels, preds)

    logging.info(f'Accuracy: {accuracy}')
    logging.info(f'Precision: {precision}')
    logging.info(f'Recall: {recall}')
    logging.info(f'Fail rate: {fail_rate}')
    


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_all_evaluations()
