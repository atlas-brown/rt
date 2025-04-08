import json
import argparse
import difflib
import os

# Assuming the 'stream' module is available and has a class ShellParser.
# Each ShellParser instance should have an attribute 'pipeline_nodes',
# where each node provides a .pretty() method and an .items attribute.
from stream.shell_parser import ShellParser
import csv

def parse_time(time_str):
    if time_str.endswith('s'):
        return float(time_str[:-1])
    return float(time_str)

def main(evaluation_result_file, csv_path):
    
    #evaluation_result_file = "./evaluation_results/ann:y_heuristic:y/evaluation_results.json"

    with open(evaluation_result_file, 'r') as f:
        data = json.load(f)
    
    lengths = []
    times = []
    
    for result in data.get('evaluation_results', []):
        address = result.get('address')
        time_val = parse_time(result.get('evaluation_time', "0s"))
        
        shell_parser = ShellParser(address)
        
        best_similarity = -1.0
        best_node_length = 0
        
        for node in shell_parser.pipeline_nodes:
            node_str = node.pretty()
            similarity = difflib.SequenceMatcher(None, "", node_str).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
                best_node_length = len(node.items)
        
        lengths.append(best_node_length)
        times.append(time_val)
    
    # Write pairs to CSV
    #csv_path = "evaluation_results/ann:y_heuristic:y/length_time_pairs.csv"
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Length', 'Time'])  # Header
        for length, time in zip(lengths, times):
            writer.writerow([length, time])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process evaluation results and output length-time pairs to a CSV file.")
    parser.add_argument('evaluation_result_file', type=str, help="Path to the evaluation results JSON file.")
    parser.add_argument('csv_path', type=str, help="Path to the output CSV file.")
    args = parser.parse_args()

    main(args.evaluation_result_file, args.csv_path)
