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

def main(evaluation_result_file, baseline_csv, length_time_csv, stats_csv):
    
    #evaluation_result_file = "./evaluation_results/ann:y_heuristic:y/evaluation_results.json"

    with open(evaluation_result_file, 'r') as f:
        data = json.load(f)
    
    lengths = []
    times = []
    
    for result in data.get('evaluation_results', []):
        address = result.get('address')
        time_val = parse_time(result.get('evaluation_time', "0s"))
        times.append(time_val)
        
        try:
            raise Exception()
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
        except Exception as e:
            #print(f"Error parsing {address}: {e}")
            lengths.append(-1)
    
    # Write pairs to CSV
    #length_time_csv = "evaluation_results/ann:y_heuristic:y/length_time_pairs.csv"
    with open(length_time_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Length', 'Time'])  # Header
        for length, time in zip(lengths, times):
            writer.writerow([length, time])

    # calculate mean, min, max time stats
    # load baseline data; columns are
    # pipeline_file,pipeline,is buggy?,shell check warning?,ltsh warning?,shell check processing time,ltsh processing time,shell check links
    shell_check_times = []
    ltsh_times = []

    with open(baseline_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            shell_check_time = parse_time(row.get('shell check processing time', '0s'))
            ltsh_time = parse_time(row.get('ltsh processing time', '0s'))
            shell_check_times.append(shell_check_time)
            ltsh_times.append(ltsh_time)

    shell_check_stats = stats(shell_check_times)
    ltsh_stats = stats(ltsh_times)
    shtreams_stats = stats(times)

    # Write stats to CSV
    with open(stats_csv, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['System', 'Mean', 'Min', 'Max'])  # Header
        writer.writerow(['shtreams', *shtreams_stats])
        writer.writerow(['sc', *shell_check_stats])
        writer.writerow(['ltsh', *ltsh_stats])



def stats(times):
    if not times:
        return 0, 0, 0

    mean_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    return mean_time, min_time, max_time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process evaluation results and output length-time pairs to a CSV file.")
    parser.add_argument('evaluation_result_file', type=str, help="Path to the evaluation results JSON file.")
    parser.add_argument('baseline_csv', type=str, help="Path to the baseline CSV file.")
    parser.add_argument('length_time_csv', type=str, help="Path to the length/time output CSV file.")
    parser.add_argument('stats_csv', type=str, help="Path to the stats output CSV file.")
    args = parser.parse_args()

    main(args.evaluation_result_file, args.baseline_csv, args.length_time_csv, args.stats_csv)
