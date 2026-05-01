import json
import argparse
import csv

def parse_time(time_str):
    if time_str.endswith('s'):
        return float(time_str[:-1])
    return float(time_str)

def main(evaluation_result_file, baseline_csv, length_time_csv, stats_csv):
    with open(evaluation_result_file, 'r') as f:
        data = json.load(f)
    
    lengths = []
    times = []
    
    for result in data.get('evaluation_results', []):
        time_val = result.get('evaluation_time')
        if time_val == "0s":
            continue
        time_val = parse_time(time_val)
        times.append(time_val)
        
        # Length is kept as the historical placeholder because the full
        # pipeline already records real pipeline lengths in evaluation JSON.
        lengths.append(-1)
    
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
    rt_stats = stats(times)

    # Write stats to CSV
    with open(stats_csv, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['System', 'Mean', 'Min', 'Max'])  # Header
        writer.writerow(['RT', *rt_stats])
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
