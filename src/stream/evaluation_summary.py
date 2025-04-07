import argparse
import json
import os
import csv
import re
from stream.config import CONFIG

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

def load_baseline_results(csv_path):
    rows = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        for row in csv.reader(f, delimiter=','):
            rows.append(row)
    return rows[1:] # drop header

def load_merged_results(ann_json_path, raw_json_path, baseline_csv_path=None):
    results_ann = load_results(ann_json_path)
    results_raw = load_results(raw_json_path)
    baseline = load_baseline_results(baseline_csv_path) if baseline_csv_path else None
    merged = {}
    for rec in results_raw:
        addr = rec["address"]
        merged.setdefault(addr, {})["raw"] = rec
    for rec in results_ann:
        addr = rec["address"]
        merged.setdefault(addr, {})["ann"] = rec
    if baseline:
        for row in baseline:
            addr = row[0]
            addr = addr if addr in merged else './' + addr
            if addr not in merged:
                continue
            info = {
                'is buggy?': row[1].lower() == 'true',
                "sc warning?": row[2].lower() == 'true',
                "ltsh warning?": row[3].lower() == 'true',
                "sc time": float(row[4]),
                "ltsh time": float(row[5])
            }
            merged[addr]["raw"]["baseline"] = info
            merged[addr]["ann"]["baseline"] = info

    for addr, recs in merged.items():
        recs["benchmark_set"] = path_to_benchmark_set(addr)
        if recs.get("ann") is None or recs.get("raw") is None:
            print(f"Missing record for {addr}: {'ann' if recs.get('ann') is None else 'raw'}")
        assert recs["raw"]["is buggy?"] == recs["ann"]["is buggy?"]
        if baseline:
            if recs["ann"].get("baseline") is None:
                print(f"Missing baseline data for {addr}")
                assert False
            assert recs["ann"]["is buggy?"] == recs["ann"]["baseline"]["is buggy?"], f"buggy label mismatch between eval results and baseline: {recs['ann']}"
            assert recs["raw"]["is buggy?"] == recs["raw"]["baseline"]["is buggy?"], f"buggy label mismatch between eval results and baseline: {recs['raw']}"

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

def results_to_overview_csv(ann_json_path, raw_json_path, baseline_csv_path, out_path):
    merged = load_merged_results(ann_json_path, raw_json_path, baseline_csv_path)
    header = ['Benchmark set', '# Correct', '# Incorrect', 'With Annotations?', 'False Results', 'Accuracy', 'Recall', 'Precision', 'F1', 'SC False', 'SC Accuracy', 'SC Precision', 'SC Recall', 'SC F1', 'LT False', 'LT Accuracy', 'LT Precision', 'LT Recall', 'LT F1', 'Status']

    benchmark_sets = set(recs["benchmark_set"] for recs in merged.values())
    rows = []
    plot_rows = []
    for ann in ["ann", "raw"]:
        for benchmark_set in benchmark_sets:
            benchmark_set_results = [recs[ann] for recs in merged.values() if recs["benchmark_set"] == benchmark_set]
            correct_benchmarks = [recs for recs in benchmark_set_results if not recs["is buggy?"]]
            buggy_benchmarks = [recs for recs in benchmark_set_results if recs["is buggy?"]]

            stats = {}
            for key, data in {"all": benchmark_set_results,
                              "correct": correct_benchmarks,
                              "buggy": buggy_benchmarks,
                              "lt": ([r["baseline"] for r in benchmark_set_results], "ltsh warning?"),
                              "sc": ([r["baseline"] for r in benchmark_set_results], "sc warning?")}.items():
                if isinstance(data, tuple):
                    stats[key] = recall_precision_f1(data[0], data[1])
                else:
                    stats[key] = recall_precision_f1(data)
            assert stats["correct"]["false_negatives"] == 0
            assert stats["buggy"]["false_positives"] == 0
            overall = {
                'Benchmark set': benchmark_set,
                '# Correct': len(correct_benchmarks),
                '# Incorrect': len(buggy_benchmarks),
                'With Annotations?': ann == "ann",
                'False Results': stats["all"]["false_positives"] + stats["all"]["false_negatives"],
                'Accuracy': stats["all"]["accuracy"],
                'Recall': stats["all"]["recall"],
                'Precision': stats["all"]["precision"],
                'F1': stats["all"]["f1"],
                'SC Precision': stats["sc"]["precision"],
                'SC Recall': stats["sc"]["recall"],
                'SC F1': stats["sc"]["f1"],
                'SC False': stats["sc"]["false_positives"] + stats["sc"]["false_negatives"],
                'SC Accuracy': stats["sc"]["accuracy"],
                'LT Precision': stats["lt"]["precision"],
                'LT Recall': stats["lt"]["recall"],
                'LT F1': stats["lt"]["f1"],
                'LT False': stats["lt"]["false_positives"] + stats["lt"]["false_negatives"],
                'LT Accuracy': stats["lt"]["accuracy"],
                'Status': 'Included'
            }
            rows.append(overall)
            # plot_rows.append(overall)
            # rows.append({# a row for just the correct benchmarks
            #     'Benchmark set': '',
            #     '# Correct': len(correct_benchmarks),
            #     '# Incorrect': 0,
            #     'With Annotations?': ann == "ann",
            #     'False Results': stats["correct"]["false_positives"],
            #     'Recall': '',
            #     'Precision': '',
            #     'F1': '',
            #     'SC Precision': '',
            #     'SC Recall': '',
            #     'SC F1': '',
            #     'SC False': '',
            #     'LT Precision': '',
            #     'LT Recall': '',
            #     'LT F1': '',
            #     'LT False': '',
            #     'Status': 'Included'
            # })
            # rows.append({# a row for just the buggy benchmarks
            #     'Benchmark set': '',
            #     '# Correct': 0,
            #     '# Incorrect': len(buggy_benchmarks),
            #     'With Annotations?': ann == "ann",
            #     'False Results': stats["buggy"]["false_negatives"],
            #     'Recall': '',
            #     'Precision': '',
            #     'F1': '',
            #     'SC Precision': '',
            #     'SC Recall': '',
            #     'SC F1': '',
            #     'SC False': '',
            #     'LT Precision': '',
            #     'LT Recall': '',
            #     'LT F1': '',
            #     'LT False': '',
            #     'Status': 'Included'
            # })
        # append a blank row between the two annotations
        rows.append({key: '' for key in header})
        # plot_rows.append({key: '' for key in header})
    
    # rows.append({key: '' for key in header})
    # rows.append({key: '' for key in header})
    write_csv(rows + plot_rows, header, out_path)

def recall_precision_f1(benchmark_results, signaled_key="warning signaled?"):
    # each benchmark_result is a dictionary with the keys "warning signaled?" and "is buggy?"
    # the prediction of the system is in the field "warning signaled?"; the prediction is correct if "is buggy?" and "warning signaled?" are the same

    # LL: these metrics are perhaps not very helpful in our breakdown by benchmark set, because some sets have no pos or neg examples
    # Something like Accuracy does not depend on having one or the other (as opposed to recall, false-pos-rate, and precision, which do)
    true_positives = sum(1 for rec in benchmark_results if rec[signaled_key] and rec["is buggy?"])
    false_positives = sum(1 for rec in benchmark_results if rec[signaled_key] and not rec["is buggy?"])
    false_negatives = sum(1 for rec in benchmark_results if not rec[signaled_key] and rec["is buggy?"])

    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    accuracy = sum(1 for rec in benchmark_results if rec[signaled_key] == rec["is buggy?"]) / len(benchmark_results) if len(benchmark_results) > 0 else 0

    return {
        "recall": recall,
        "precision": precision,
        "f1": f1,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "accuracy": accuracy
    }

benchmark_mapping = None
def path_to_benchmark_set(collection):
    global benchmark_mapping
    if not benchmark_mapping:
        benchmark_mapping = CONFIG.get("benchmark names")
    for key, value in benchmark_mapping.items():
        if re.search(key, collection):
            return value


def merged_csv_to_bug_detection(ann_json_path, raw_json_path, baseline_csv_path, out_path, eprint_records=False):
    merged = load_merged_results(ann_json_path, raw_json_path, baseline_csv_path)
    # [shtreams?, SC?, LT?]
    data = {(us, sc, lt): 0 for us in [True, False] for sc in [True, False] for lt in [True, False]}
    header = ['System', 'Only this detects', 'and Shtreams', 'and SC', 'and LT', 'All']
    # only raw for a fair comparison
    for recs in merged.values():
        if not recs["raw"]["baseline"]["is buggy?"]:
            continue
        key = (recs["raw"]["warning signaled?"],
               recs["raw"]["baseline"]["sc warning?"],
               recs["raw"]["baseline"]["ltsh warning?"])
        if recs["raw"]["warning signaled?"] is None:
            print("crash!: " + str(recs))
            key = (False, key[1], key[2])
        data[key] += 1
        if eprint_records:
            print(f"{key}#{recs}")

    def get(us, sc, lt):
        return data[(us == 1, sc == 1, lt ==1)]

    rows = []
    rows.append({"System": "Shtreams",
                 "Only this detects": get(1, 0, 0),
                 "and Shtreams": 0,
                 "and SC": get(1, 1, 0),
                 "and LT": get(1, 0, 1),
                 "All": get(1, 1, 1)})
    rows.append({"System": "ShellCheck",
                 "Only this detects": get(0, 1, 0),
                 "and Shtreams": get(1, 1, 0),
                 "and SC": 0,
                 "and LT": get(0, 1, 1),
                 "All": get(1, 1, 1)})
    rows.append({"System": "LadderTypes",
                 "Only this detects": get(0, 0, 1),
                 "and Shtreams": get(1, 0, 1),
                 "and SC": get(0, 1, 1),
                 "and LT": 0,
                 "All": get(1, 1, 1)})
    write_csv(rows, header, out_path)


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
    parser.add_argument('--baseline_csv', type=str, default='evaluation_results/baseline.csv',
                        help='Path to baseline results CSV file (default: evaluation_results/baseline.csv)')
    parser.add_argument('--merged_csv', type=str, default='evaluation_results/merged_results.csv',
                        help='Path to merged CSV file (default: evaluation_results/merged_results.csv)')
    parser.add_argument('--bug_detection_csv', type=str, default='evaluation_results/bug_detection.csv',
                        help='Path to bug detection CSV file to write (default: evaluation_results/bug_detection.csv)')
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
        results_to_overview_csv(args.ann_json, args.raw_json, args.baseline_csv, args.overview_csv)
        merged_csv_to_bug_detection(args.ann_json, args.raw_json, args.baseline_csv, args.bug_detection_csv,eprint_records=True)

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
