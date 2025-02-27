import argparse
import json
import os
import csv
import re

def convert_to_github_address(address):
    if address.startswith('./'):
        address = address[2:]
    parts = address.split('/')
    collection = '/'.join(parts[:-1])
    benchmark = "https://github.com/brown-cs2952r/StreamTypes/blob/main/" + address
    return benchmark, collection

def process_runtime_error(error):
    return error if error is not None else ''

def process_category(category):
    return '' if category is None or category == '<missing>' else category

def process_content(content):
    if content is None:
        return ''
    s = content.replace('\n', ' ')
    return s[:300] + '...' if len(s) > 300 else s

def compute_correct_result(record):
    return record["warning signaled?"] == record["is buggy?"] if "warning signaled?" in record and "is buggy?" in record else ''

def write_csv(rows, header, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def results_to_summary_csv(json_path, out_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        results = json.load(f)["evaluation_results"]
    results.sort(key=lambda x: x["address"])
    header = ['Benchmark', 'Collection', 'Tag', 'Buggy?', 'Correct Result?', 'Time(s)', 'RunTime Error', 'Category', 'Notes', 'Pipeline']
    rows = []
    for result in results:
        benchmark, collection = convert_to_github_address(result["address"])
        row = {
            'Benchmark': benchmark,
            'Collection': collection,
            'Tag': category_to_tag(compute_correct_result(result), process_category(result["category"])),
            'Buggy?': result["is buggy?"],
            'Correct Result?': compute_correct_result(result),
            'Time(s)': result["evaluation_time"],
            'RunTime Error': process_runtime_error(result["tool runtime error"]),
            'Category': process_category(result["category"]),
            'Notes': result["notes"],
            'Pipeline': process_content(result["content"])
        }
        rows.append(row)
    write_csv(rows, header, out_path)

def load_results(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)["evaluation_results"]

def load_merged_results(ann_json_path, raw_json_path):
    results_ann = load_results(ann_json_path)
    results_raw = load_results(raw_json_path)
    merged = {}
    for rec in results_raw:
        addr = rec["address"]
        merged.setdefault(addr, {})["raw"] = rec
    for rec in results_ann:
        addr = rec["address"]
        merged.setdefault(addr, {})["ann"] = rec
    return merged

def results_to_merged_csv(ann_json_path, raw_json_path, out_path):
    merged = load_merged_results(ann_json_path, raw_json_path)
    header = [
        'Benchmark', 'Collection', 'Pipeline',
        'Raw Buggy?', 'Raw Correct Result?', 'Raw Time(s)', 'Raw RunTime Error', 'Raw Category', 'Raw Notes',
        'Ann Buggy?', 'Ann Correct Result?', 'Ann Time(s)', 'Ann RunTime Error', 'Ann Category', 'Ann Notes'
    ]
    rows = []
    for addr, recs in merged.items():
        common_rec = recs.get("ann") or recs.get("raw")
        benchmark, collection = convert_to_github_address(common_rec["address"])
        pipeline = process_content(common_rec["content"])
        raw_rec = recs.get("raw")
        ann_rec = recs.get("ann")
        row = {
            'Benchmark': benchmark,
            'Collection': collection,
            'Pipeline': pipeline,
            'Raw Buggy?': raw_rec["is buggy?"] if raw_rec else '',
            'Raw Correct Result?': compute_correct_result(raw_rec) if raw_rec else '',
            'Raw Time(s)': raw_rec["evaluation_time"] if raw_rec else '',
            'Raw RunTime Error': process_runtime_error(raw_rec.get("tool runtime error")) if raw_rec else '',
            'Raw Category': process_category(raw_rec.get("category")) if raw_rec else '',
            'Raw Notes': raw_rec["notes"] if raw_rec else '',
            'Ann Buggy?': ann_rec["is buggy?"] if ann_rec else '',
            'Ann Correct Result?': compute_correct_result(ann_rec) if ann_rec else '',
            'Ann Time(s)': ann_rec["evaluation_time"] if ann_rec else '',
            'Ann RunTime Error': process_runtime_error(ann_rec.get("tool runtime error")) if ann_rec else '',
            'Ann Category': process_category(ann_rec.get("category")) if ann_rec else '',
            'Ann Notes': ann_rec["notes"] if ann_rec else ''
        }
        rows.append(row)
    rows.sort(key=lambda x: x["Benchmark"])
    write_csv(rows, header, out_path)

def results_to_overview_csv(ann_json_path, raw_json_path, out_path):
    merged = load_merged_results(ann_json_path, raw_json_path)
    header = ['Benchmark set', '# Correct', '# Incorrect', 'With Annotations?', 'False Results', 'Recall', 'Precision', 'F1', 'ShellCheck F1', 'ShellCheck False', 'Ladder F1', 'Ladder False', 'Status']
    for addr, recs in merged.items():
        recs["benchmark_set"] = path_to_benchmark_set(addr)
        if recs.get("ann") is None or recs.get("raw") is None:
            print(f"Missing record for {addr}: {'ann' if recs.get('ann') is None else 'raw'}")

    benchmark_sets = set(recs["benchmark_set"] for recs in merged.values())
    rows = []
    for ann in ["ann", "raw"]:
        for benchmark_set in benchmark_sets:
            benchmark_set_results = [recs[ann] for recs in merged.values() if recs["benchmark_set"] == benchmark_set]
            correct_benchmarks = [recs for recs in benchmark_set_results if not recs["is buggy?"]]
            buggy_benchmarks = [recs for recs in benchmark_set_results if recs["is buggy?"]]

            
            recall, precision, f1, false_positives, false_negatives = recall_precision_f1(benchmark_set_results)
            recall_correct, precision_correct, f1_correct, false_positives_correct, false_negatives_correct = recall_precision_f1(correct_benchmarks)
            recall_buggy, precision_buggy, f1_buggy, false_positives_buggy, false_negatives_buggy = recall_precision_f1(buggy_benchmarks)
            assert false_negatives_correct == 0
            assert false_positives_buggy == 0
            rows.append({
                'Benchmark set': benchmark_set,
                '# Correct': len(correct_benchmarks),
                '# Incorrect': len(buggy_benchmarks),
                'With Annotations?': ann == "ann",
                'False Results': false_positives + false_negatives,
                'Recall': recall,
                'Precision': precision,
                'F1': f1,
                'ShellCheck F1': 'todo',  # Placeholder for ShellCheck F1
                'ShellCheck False': 'todo',  # Placeholder for ShellCheck False
                'Ladder F1': 'todo',  # Placeholder for Ladder F1
                'Ladder False': 'todo',  # Placeholder for Ladder False
                'Status': 'Included'  # Placeholder for status
            })
            rows.append({# a row for just the correct benchmarks
                'Benchmark set': '',
                '# Correct': len(correct_benchmarks),
                '# Incorrect': 0,
                'With Annotations?': ann == "ann",
                'False Results': false_positives_correct,
                'Recall': '',
                'Precision': '',
                'F1': '',
                'ShellCheck F1': 'todo',  # Placeholder for ShellCheck F1
                'ShellCheck False': 'todo',  # Placeholder for ShellCheck False
                'Ladder F1': 'todo',  # Placeholder for Ladder F1
                'Ladder False': 'todo',  # Placeholder for Ladder False
                'Status': 'Included'  # Placeholder for status
            })
            rows.append({# a row for just the buggy benchmarks
                'Benchmark set': '',
                '# Correct': 0,
                '# Incorrect': len(buggy_benchmarks),
                'With Annotations?': ann == "ann",
                'False Results': false_negatives_buggy,
                'Recall': '',
                'Precision': '',
                'F1': '',
                'ShellCheck F1': 'todo',  # Placeholder for ShellCheck F1
                'ShellCheck False': 'todo',  # Placeholder for ShellCheck False
                'Ladder F1': 'todo',  # Placeholder for Ladder F1
                'Ladder False': 'todo',  # Placeholder for Ladder False
                'Status': 'Included'  # Placeholder for status
            })
        # append a blank row between the two annotations
        rows.append({key: '' for key in header})
    
    write_csv(rows, header, out_path)

def recall_precision_f1(benchmark_results):
    # each benchmark_result is a dictionary with the keys "warning signaled?" and "is buggy?"
    # the prediction of the system is in the field "warning signaled?"; the prediction is correct if "is buggy?" and "warning signaled?" are the same
    true_positives = sum(1 for rec in benchmark_results if rec["warning signaled?"] == rec["is buggy?"])
    false_positives = sum(1 for rec in benchmark_results if rec["warning signaled?"] and not rec["is buggy?"])
    false_negatives = sum(1 for rec in benchmark_results if not rec["warning signaled?"] and rec["is buggy?"])

    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return recall, precision, f1, false_positives, false_negatives

benchmark_mapping = None
def path_to_benchmark_set(collection):
    global benchmark_mapping
    if not benchmark_mapping:
        with open("./src/stream/benchmark_mapping.json", "r") as file:
            benchmark_mapping = json.load(file)
    for key, value in benchmark_mapping.items():
        if re.search(key, collection):
            return value


def main():
    parser = argparse.ArgumentParser(description='Process evaluation results from JSON and generate CSV summaries.')
    parser.add_argument('--mode', type=str, choices=['separate', 'merged', 'all'], default='all',
                        help='Mode: separate - generate CSV for with_annotations and raw separately; merged - merge two JSON files into one CSV; all - generate both separate and merged CSV files.')
    parser.add_argument('--ann_json', type=str, default='evaluation_results/with_annotations/evaluation_results.json',
                        help='Path to with_annotations JSON file (default: evaluation_results/with_annotations/evaluation_results.json)')
    parser.add_argument('--ann_csv', type=str, default='evaluation_results/with_annotations/results.csv',
                        help='Path to with_annotations CSV file (default: evaluation_results/with_annotations/results.csv)')
    parser.add_argument('--raw_json', type=str, default='evaluation_results/raw/evaluation_results.json',
                        help='Path to raw JSON file (default: evaluation_results/raw/evaluation_results.json)')
    parser.add_argument('--raw_csv', type=str, default='evaluation_results/raw/results.csv',
                        help='Path to raw CSV file (default: evaluation_results/raw/results.csv)')
    parser.add_argument('--merged_csv', type=str, default='evaluation_results/merged_results.csv',
                        help='Path to merged CSV file (default: evaluation_results/merged_results.csv)')
    parser.add_argument('--overview_csv', type=str, default='evaluation_results/overview_results.csv',
                        help='Path to overview CSV file (default: evaluation_results/overview_results.csv)')
    args = parser.parse_args()
    if args.mode in ['separate', 'all']:
        print(f"Generating separate CSV files: {args.ann_csv} and {args.raw_csv}")
        results_to_summary_csv(args.ann_json, args.ann_csv)
        results_to_summary_csv(args.raw_json, args.raw_csv)
    if args.mode in ['merged', 'all']:
        print(f"Generating merged CSV file: {args.merged_csv}")
        results_to_merged_csv(args.ann_json, args.raw_json, args.merged_csv)
        print(f"Generating overview CSV file: {args.overview_csv}")
        results_to_overview_csv(args.ann_json, args.raw_json, args.overview_csv)

def category_to_tag(is_correct: bool, category: str):
    if is_correct:
        return ""
    with open("./src/stream/category_to_tag.json", "r") as file:
        mapping = json.load(file)
    mapping.sort(key=lambda x: x["priority"])
    for entry in mapping:
        if entry["category"] in category:
            return entry["tag"]
    return ""

if __name__ == "__main__":
    main()
