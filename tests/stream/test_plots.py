import math
import os

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from stream.scripts.plots import build_accuracy_chart_data, plot_accuracy, plot_accuracy_charts


def test_build_accuracy_chart_data_uses_weighted_buggy_and_correct_aggregates_per_panel():
    data = pd.DataFrame([
        {"Benchmark set": "Alpha", "With Annotations?": True, "# Incorrect": 3, "# Correct": 1, "Accuracy": 0.5, "SC Accuracy": 0.2, "LT Accuracy": 0.4},
        {"Benchmark set": "Beta", "With Annotations?": True, "# Incorrect": 2, "# Correct": 4, "Accuracy": 0.9, "SC Accuracy": 0.8, "LT Accuracy": 0.6},
        {"Benchmark set": "Alpha (buggy)", "With Annotations?": True, "# Incorrect": 3, "# Correct": 0, "Accuracy": 0.5, "SC Accuracy": 0.2, "LT Accuracy": 0.4},
        {"Benchmark set": "Beta (correct)", "With Annotations?": True, "# Incorrect": 0, "# Correct": 4, "Accuracy": 1.0, "SC Accuracy": 0.9, "LT Accuracy": 0.8},
        {"Benchmark set": "Gamma (buggy)", "With Annotations?": True, "# Incorrect": 1, "# Correct": 0, "Accuracy": 0.9, "SC Accuracy": 0.8, "LT Accuracy": 0.6},
        {"Benchmark set": "Alpha (buggy)", "With Annotations?": False, "# Incorrect": 5, "# Correct": 0, "Accuracy": 0.2, "SC Accuracy": 0.1, "LT Accuracy": 0.3},
        {"Benchmark set": "Alpha", "With Annotations?": False, "# Incorrect": 5, "# Correct": 0, "Accuracy": 0.2, "SC Accuracy": 0.1, "LT Accuracy": 0.3},
        {"Benchmark set": "Beta", "With Annotations?": False, "# Incorrect": 2, "# Correct": 3, "Accuracy": 0.4, "SC Accuracy": 0.3, "LT Accuracy": 0.5},
        {"Benchmark set": "Gamma (correct)", "With Annotations?": False, "# Incorrect": 0, "# Correct": 1, "Accuracy": 0.8, "SC Accuracy": 0.75, "LT Accuracy": 0.7},
        {"Benchmark set": "Delta (buggy)", "With Annotations?": False, "# Incorrect": 5, "# Correct": 0, "Accuracy": 0.4, "SC Accuracy": 0.3, "LT Accuracy": 0.5},
    ])

    annotated_plot_data = build_accuracy_chart_data(data, True)

    assert math.isclose(annotated_plot_data["Buggy"]["RT"], 0.6)
    assert math.isclose(annotated_plot_data["Buggy"]["ShellCheck"], 0.35)
    assert math.isclose(annotated_plot_data["Buggy"]["LadderTypes"], 0.45)
    assert math.isclose(annotated_plot_data["Correct"]["RT"], 1.0)
    assert math.isclose(annotated_plot_data["Correct"]["ShellCheck"], 0.9)
    assert math.isclose(annotated_plot_data["Correct"]["LadderTypes"], 0.8)

    raw_plot_data = build_accuracy_chart_data(data, False)

    assert math.isclose(raw_plot_data["Buggy"]["RT"], 0.3)
    assert math.isclose(raw_plot_data["Buggy"]["ShellCheck"], 0.2)
    assert math.isclose(raw_plot_data["Buggy"]["LadderTypes"], 0.4)
    assert math.isclose(raw_plot_data["Correct"]["RT"], 0.8)
    assert math.isclose(raw_plot_data["Correct"]["ShellCheck"], 0.75)
    assert math.isclose(raw_plot_data["Correct"]["LadderTypes"], 0.7)


def test_plot_accuracy_renders_single_annotation_panel(tmp_path):
    data = pd.DataFrame([
        {"Benchmark set": "Alpha (buggy)", "With Annotations?": True, "# Incorrect": 2, "# Correct": 0, "Accuracy": 0.7, "SC Accuracy": 0.2, "LT Accuracy": 0.3},
        {"Benchmark set": "Beta (correct)", "With Annotations?": True, "# Incorrect": 0, "# Correct": 4, "Accuracy": 0.95, "SC Accuracy": 0.9, "LT Accuracy": 0.97},
        {"Benchmark set": "Gamma (buggy)", "With Annotations?": True, "# Incorrect": 1, "# Correct": 0, "Accuracy": 0.4, "SC Accuracy": 0.1, "LT Accuracy": 0.2},
        {"Benchmark set": "Alpha (buggy)", "With Annotations?": False, "# Incorrect": 2, "# Correct": 0, "Accuracy": 0.4, "SC Accuracy": 0.1, "LT Accuracy": 0.2},
        {"Benchmark set": "Beta (correct)", "With Annotations?": False, "# Incorrect": 0, "# Correct": 4, "Accuracy": 0.85, "SC Accuracy": 0.8, "LT Accuracy": 0.88},
    ])

    fig, ax = plot_accuracy(data, tmp_path / "accuracy-chart-with-annotations.pdf", True)

    assert len(ax.patches) == 6
    assert [tick.get_text() for tick in ax.get_xticklabels()] == [
        "RT", "ShellCheck", "LadderTypes",
        "RT", "ShellCheck", "LadderTypes",
    ]
    assert [text.get_text() for text in ax.texts] == ["Buggy", "Correct"]
    assert ax.get_ylabel() == "Accuracy"
    assert ax.get_legend() is None

    plt.close(fig)


def test_plot_accuracy_charts_writes_two_separate_files(tmp_path):
    data = pd.DataFrame([
        {"Benchmark set": "Alpha (buggy)", "With Annotations?": True, "# Incorrect": 2, "# Correct": 0, "Accuracy": 0.7, "SC Accuracy": 0.2, "LT Accuracy": 0.3},
        {"Benchmark set": "Beta (correct)", "With Annotations?": True, "# Incorrect": 0, "# Correct": 4, "Accuracy": 0.95, "SC Accuracy": 0.9, "LT Accuracy": 0.97},
        {"Benchmark set": "Alpha (buggy)", "With Annotations?": False, "# Incorrect": 2, "# Correct": 0, "Accuracy": 0.4, "SC Accuracy": 0.1, "LT Accuracy": 0.2},
        {"Benchmark set": "Beta (correct)", "With Annotations?": False, "# Incorrect": 0, "# Correct": 4, "Accuracy": 0.85, "SC Accuracy": 0.8, "LT Accuracy": 0.88},
    ])

    outputs = plot_accuracy_charts(data, tmp_path)

    assert [os.path.basename(path) for path, _, _ in outputs] == [
        "accuracy-chart-with-annotations.pdf",
        "accuracy-chart-without-annotations.pdf",
    ]
    for path, fig, _ in outputs:
        assert os.path.exists(path)
        plt.close(fig)
