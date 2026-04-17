import argparse
import pandas as pd
import numpy as np
import os

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

ACCURACY_PANELS = (
    (True, "accuracy-chart-with-annotations.pdf"),
    (False, "accuracy-chart-without-annotations.pdf"),
)
ACCURACY_SYSTEMS = ("Rt", "ShellCheck", "LadderTypes")
ACCURACY_COLORS = {
    "Rt": "#8B1E3F",
    "ShellCheck": "#BE9832",
    "LadderTypes": "#9EDCF0",
}
ACCURACY_X_POSITIONS = np.array([0, 1, 2, 5, 6, 7], dtype=float)

def _weighted_metric(rows, metric_column, weight_column):
    if rows.empty:
        return 0.0

    weights = pd.to_numeric(rows[weight_column], errors="coerce").fillna(0)
    values = pd.to_numeric(rows[metric_column], errors="coerce").fillna(0)
    valid_rows = weights > 0
    if not valid_rows.any():
        return 0.0

    return float(np.average(values[valid_rows], weights=weights[valid_rows]))

def _weighted_metric_with_weights(rows, metric_column, weights):
    if rows.empty:
        return 0.0

    metric_values = pd.to_numeric(rows[metric_column], errors="coerce").fillna(0)
    numeric_weights = pd.to_numeric(weights, errors="coerce").fillna(0)
    valid_rows = numeric_weights > 0
    if not valid_rows.any():
        return 0.0

    return float(np.average(metric_values[valid_rows], weights=numeric_weights[valid_rows]))

def build_accuracy_chart_data(data, with_annotations):
    annotation_mask = data["With Annotations?"].astype(str).str.lower() == str(with_annotations).lower()
    panel_rows = data[annotation_mask].copy()
    benchmark_labels = panel_rows["Benchmark set"].astype(str)
    buggy_rows = panel_rows[benchmark_labels.str.endswith(" (buggy)", na=False)]
    correct_rows = panel_rows[benchmark_labels.str.endswith(" (correct)", na=False)]

    if buggy_rows.empty or correct_rows.empty:
        raise ValueError("Accuracy plot requires '(buggy)' and '(correct)' rows for the requested annotation setting.")

    return {
        "Buggy": {
            "Rt": _weighted_metric(buggy_rows, "Accuracy", "# Incorrect"),
            "ShellCheck": _weighted_metric(buggy_rows, "SC Accuracy", "# Incorrect"),
            "LadderTypes": _weighted_metric(buggy_rows, "LT Accuracy", "# Incorrect"),
        },
        "Correct": {
            "Rt": _weighted_metric(correct_rows, "Accuracy", "# Correct"),
            "ShellCheck": _weighted_metric(correct_rows, "SC Accuracy", "# Correct"),
            "LadderTypes": _weighted_metric(correct_rows, "LT Accuracy", "# Correct"),
        },
    }

def _plot_accuracy_panel(ax, plot_data):
    heights = [
        plot_data["Buggy"][system] for system in ACCURACY_SYSTEMS
    ] + [
        plot_data["Correct"][system] for system in ACCURACY_SYSTEMS
    ]
    labels = list(ACCURACY_SYSTEMS) * 2
    colors = [ACCURACY_COLORS[system] for system in labels]

    ax.set_axisbelow(True)
    ax.grid(which="major", axis="both", linestyle=":", linewidth=0.9, color="#C9CDD2")
    ax.bar(
        ACCURACY_X_POSITIONS,
        heights,
        width=0.6,
        color=colors,
        edgecolor="black",
        linewidth=1.6,
        hatch="//",
        zorder=3,
    )

    ax.set_xlim(-0.7, 7.7)
    ax.set_ylim(0, 1.05)
    ax.set_yticks(np.linspace(0, 1, 6))
    ax.set_ylabel("Accuracy")
    ax.set_xticks(ACCURACY_X_POSITIONS, labels, rotation=25, ha="right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.2)
    ax.spines["bottom"].set_linewidth(1.2)
    for label, positions in {
        "Buggy": ACCURACY_X_POSITIONS[:3],
        "Correct": ACCURACY_X_POSITIONS[3:],
    }.items():
        ax.text(float(np.mean(positions)), 1.045, label, ha="center", va="bottom", fontsize=16)

def plot_accuracy(data, output_path, with_annotations):
    fig, ax = plt.subplots(figsize=(10, 4))
    plot_data = build_accuracy_chart_data(data, with_annotations)
    _plot_accuracy_panel(ax, plot_data)

    fig.tight_layout()
    fig.savefig(output_path, format="pdf")
    return fig, ax

def plot_accuracy_charts(data, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    outputs = []
    for with_annotations, filename in ACCURACY_PANELS:
        output_path = os.path.join(output_dir, filename)
        fig, ax = plot_accuracy(data, output_path, with_annotations)
        outputs.append((output_path, fig, ax))
    return outputs

def plot_bug_detection_bar(data, output_path):
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

def plot_bug_detection(data, output_path):
    from matplotlib_set_diagrams import EulerDiagram

    combination_counts = {
        (1, 0, 0): data[data["System"] == "Shtreams"]["Only this detects"].values[0],
        (1, 1, 0): data[data["System"] == "Shtreams"]["and SC"].values[0],
        (1, 0, 1): data[data["System"] == "Shtreams"]["and LT"].values[0],
        (1, 1, 1): data[data["System"] == "Shtreams"]["All"].values[0],
        (0, 1, 0): data[data["System"] == "ShellCheck"]["Only this detects"].values[0],
        (0, 1, 1): data[data["System"] == "ShellCheck"]["and LT"].values[0],
        (0, 0, 1): data[data["System"] == "LadderTypes"]["Only this detects"].values[0],
        }
    plt.figure(figsize=figsize)
    dgm = EulerDiagram(combination_counts, set_labels=[f"{sysname} (w/o anns)", "ShellCheck", "LadderTypes"], set_colors=color_scheme[1:4])
    for i, text in enumerate(dgm.set_label_artists):
        # move text to the right
        match i:
            case 0:
                text.set_position((text.get_position()[0] + 11, text.get_position()[1] - 11))
            case 1:
                text.set_position((text.get_position()[0], text.get_position()[1] - 0.85))
            case 2:
                text.set_position((text.get_position()[0] + 1.5, text.get_position()[1] + 0))
    plt.title(None)
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
        print(f"Size {x} not in any bucket")
    for x in data["automata_size"]:
        if x == 0:
            continue
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

    # Ensure the output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    plt.rcParams.update({
        #"text.usetex": True, # doesnt work in container
        "font.family": "serif",
        #"font.serif": ["Times New Roman"], # doesnt work in container
        "font.size": 12,
    })

    overview_data = load_csv(args.overview_csv)
    plot_accuracy_charts(overview_data, args.output_dir)
    plt.rc('font', size=23)
    bug_detection_data = load_csv(args.bug_detection_csv)
    plot_bug_detection(bug_detection_data, os.path.join(args.output_dir, "bug-detection.pdf"))
    plt.rc('font', size=12)
    length_time_data = load_csv(args.length_time_csv)
    plot_length_time(length_time_data, os.path.join(args.output_dir, "time-length-chart.pdf"))
    automata_data = load_csv(args.automata_csv)
    plot_automata_sizes(automata_data, os.path.join(args.output_dir, "automata-sizes.pdf"))
    

if __name__ == "__main__":
    main()
