import argparse
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

def load_csv(file_path):
    try:
        data = pd.read_csv(file_path)
        return data
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        exit(1)

color_scheme = ["#AA4465", "#FFA69E", "#998650", "#93E1D8"]
figsize = (7, 4)
sysname = "RT"

def plot_accuracy(data, output_path):
    # Filter data by annotation status
    data_ann = data[data["With Annotations?"] == True]
    data_unann = data[data["With Annotations?"] == False]

    # Get all benchmark sets
    # benchmarks = sorted(data.dropna()["Benchmark set"].unique())
    benchmarks = "Ladder PaSh Intercode LLM Mutants Handwritten StackOverflow GitHub".split()

    # Prepare bar heights
    shtreams_no_ann = [
        data_unann[data_unann["Benchmark set"] == b]["Accuracy"].values[0]
        if b in data_unann["Benchmark set"].values else 0
        for b in benchmarks
    ]
    shtreams_ann = [
        data_ann[data_ann["Benchmark set"] == b]["Accuracy"].values[0]
        if b in data_ann["Benchmark set"].values else 0
        for b in benchmarks
    ]
    shellcheck = [
        data_ann[data_ann["Benchmark set"] == b]["SC Accuracy"].values[0]
        if b in data_ann["Benchmark set"].values else 0
        for b in benchmarks
    ]
    laddertypes = [
        data_ann[data_ann["Benchmark set"] == b]["LT Accuracy"].values[0]
        if b in data_ann["Benchmark set"].values else 0
        for b in benchmarks
    ]

    x = np.arange(len(benchmarks))
    width = 0.2

    plt.figure(figsize=figsize)
    plt.rc('axes', axisbelow=True)
    plt.grid(axis='y', linestyle='-', alpha=0.7)

    plt.bar(x - 1.5*width, shtreams_no_ann, width, label=f"{sysname}", color=color_scheme[0], hatch="/")
    plt.bar(x - 0.5*width, shtreams_ann, width, label=f"{sysname} (w/ anns)", color=color_scheme[1], hatch="//")
    plt.bar(x + 0.5*width, shellcheck, width, label="ShellCheck", color=color_scheme[2], hatch="\\")
    plt.bar(x + 1.5*width, laddertypes, width, label="LadderTypes", color=color_scheme[3])

    plt.xticks(x, benchmarks, rotation=30, ha="right")
    plt.ylim(0, 1)
    plt.ylabel("Accuracy")
    plt.title(None)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=4)
    plt.tight_layout()
    plt.savefig(output_path, format="pdf")

def plot_bug_detection(data, output_path):
    systems = data["System"].unique()
    all_detected = [data[data["System"] == s]["All"].values[0] for s in systems]
    only_this_detects = [data[data["System"] == s]["Only this detects"].values[0] for s in systems]
    and_shtreams = [data[data["System"] == s]["and Shtreams"].values[0] for s in systems]
    and_sc = [data[data["System"] == s]["and SC"].values[0] for s in systems]
    and_lt = [data[data["System"] == s]["and LT"].values[0] for s in systems]

    x = np.arange(len(systems))
    plt.figure(figsize=figsize)
    plt.rc('axes', axisbelow=True)
    plt.grid(axis='y', linestyle='-', alpha=0.7)
    plt.bar(x, all_detected, label="All", color="gray")
    plt.bar(x, only_this_detects, bottom=all_detected, label="Only this detects", color=color_scheme[0], hatch="/")
    plt.bar(x, and_shtreams, bottom=np.array(all_detected) + np.array(only_this_detects), label=f"and {sysname}", color=color_scheme[1], hatch="//")
    plt.bar(x, and_sc, bottom=np.array(all_detected) + np.array(only_this_detects) + np.array(and_shtreams), label="and SC", color=color_scheme[2], hatch="\\")
    plt.bar(x, and_lt, bottom=np.array(all_detected) + np.array(only_this_detects) + np.array(and_shtreams) + np.array(and_sc), label="and LT", color=color_scheme[3])

    plt.xticks(x, [sysname, "ShellCheck", "LadderTypes"])#, rotation=40, ha="right")
    plt.ylabel("Number of bugs detected")
    plt.title(None)
    # plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.3), ncol=3)
    plt.legend(loc=(0.15, 1.025), ncol=3)
    plt.tight_layout()
    plt.savefig(output_path, format="pdf")

def plot_length_time(data, output_path):
    aggregated_data = data.groupby("Length").agg({
        "Time": "mean"
    }).reset_index()

    plt.figure(figsize=figsize)
    plt.rc('axes', axisbelow=True)
    plt.scatter(data["Length"], data["Time"], color=color_scheme[1])
    plt.scatter(aggregated_data["Length"], aggregated_data["Time"], marker="s", color=color_scheme[0])
    plt.grid(axis='y', linestyle='-', alpha=0.7)
    plt.xticks(list(range(2, 12)), list(range(2, 12)))
    plt.xlabel("Pipeline length (stages)")
    plt.ylabel("Analysis time (s)")
    plt.title(None)
    plt.tight_layout()
    plt.savefig(output_path, format="pdf")

def plot_automata_sizes(data, output_path):
    ranges = [i for i in range(1, 10)] + [(i, i+9) for i in range(10, 50, 10)] + [(50, float('inf'))]
    buckets = {b: 0 for b in ranges}
    def bucket(x):
        for b in buckets:
            match b:
                case n if n == x:
                    return b
                case (l, r) if x >= l and x <= r:
                    return b
                case _:
                    pass
    for x in data["automata_size"]:
        buckets[bucket(x)] += 1

    plt.figure(figsize=figsize)
    plt.rc('axes', axisbelow=True)
    for i, b in enumerate(ranges):
        plt.bar(i + 1, buckets[b], color=color_scheme[0])
    plt.grid(axis='y', linestyle='-', alpha=0.7)
    plt.xticks(np.arange(len(ranges) + 1),
               [""] + [str(b) for b in ranges],
               rotation=40, 
               ha="right")
    plt.xlabel("Automata size (states)")
    plt.ylabel("Pipeline count")
    plt.title(None)
    plt.tight_layout()
    plt.savefig(output_path, format="pdf")


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "overview_csv",
        type=str,
        help="Path to the input CSV file (e.g., overview.csv)."
    )
    parser.add_argument(
        "bug_detection_csv",
        type=str,
        help="Path to the input CSV file (e.g., bug_detection.csv)."
    )
    parser.add_argument(
        "length_time_csv",
        type=str,
        help="Path to the input CSV file (e.g., length_time.csv)."
    )
    parser.add_argument(
        "automata_csv",
        type=str,
        help="Path to the input CSV file (e.g., automata_sizes.csv)."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=".",
        help="Path to the output directory (default: current directory)."
    )
    return parser.parse_args()

def main():
    args = parse_arguments()

    plt.rcParams.update({
        #"text.usetex": True, # doesnt work in container
        "font.family": "serif",
        #"font.serif": ["Times New Roman"], # doesnt work in container
    })

    overview_data = load_csv(args.overview_csv)
    plot_accuracy(overview_data, args.output_dir + "/accuracy.pdf")
    bug_detection_data = load_csv(args.bug_detection_csv)
    plot_bug_detection(bug_detection_data, args.output_dir + "/bug_detection.pdf")
    length_time_data = load_csv(args.length_time_csv)
    plot_length_time(length_time_data, args.output_dir + "/length_time.pdf")
    automata_data = load_csv(args.automata_csv)
    plot_automata_sizes(automata_data, args.output_dir + "/automata_sizes.pdf")
    

if __name__ == "__main__":
    main()