import matplotlib.pyplot as plt
import json
import numpy as np

title = "Shseer performance over versions"
outfile1 = "graph_progress_perf.png"
outfile2 = "graph_progress_acc.png"

if __name__ == "__main__":
    # Get the versions data
    filepath = "./versions_overtime.json"
    with open(filepath, "r") as f:
        data = f.read()
        if data == "":
            old_version = []
        else:
            old_versions = json.loads(data)
    
    # Append to x and y for the time_per_line
    x = []
    y = []
    for version in old_versions:
        x.append(version)
        y.append(old_versions[version]["average_time_per_line"])

    # Draw the graph
    fig = plt.figure(figsize=(8, 8))
    plt.suptitle("Shseer Average Time per LOC")
    plt.title(title)
    plt.xlabel("Version")
    plt.ylabel("Average time per LOC (us)")
    plt.plot(x, y, marker='o')
    plt.ylim((0, max(y) * 1.1))
    plt.savefig(outfile1)
    plt.show()

    # Append to x and y for the percent makeup
    x = []
    y = []
    totals = []
    labels = ["Positive Scripts", "Negative Scripts", "Panicked Scrips", "Timed-out Scripts"]
    for version in old_versions:
        x.append(version)
        v = old_versions[version]
        total = v["scripts_total"]
        if total == 0:
            print("No scripts tested")
            exit(1) # no scripts tested
        good = v["scripts_good"] * 100
        bad = v["scripts_bad"] * 100
        panic = v["scripts_panic"] * 100
        timeout = v["scripts_timeout"] * 100
        y.append((good / total, bad / total, panic / total, timeout / total))
        totals.append(total)

    # Start on good, bad, and the panic
    fig = plt.figure(figsize=(8, 8))
    plt.suptitle("Shseer Percent Found")
    plt.title(title)
    plt.xlabel("Version")
    plt.ylabel("Percent makeup of scripts (%)")
    plt.ylim((0, 110))
    last = [0] * len(x) # last is just an array of 0s to be the bottom
    colors = ["#1F77B4", "#9467BD", "#D0E9F8", "#1BC6B4"]
    for i in range(4): # add the bars in a stacked formation
        now = [v[i] for v in y] # now is the current status (good, bad, panic, or timeout)
        plt.bar(x, now, color=colors[i], bottom=last, width=0.2, label=f"{labels[i]}")
        last = [last[i] + now[i] for i in range(len(now))] # last accumulates all the previous to be used as the bottom
    
    # Add text information
    bar_pos = np.arange(len(x)) # bar positions
    for i in range(len(totals)):
        # Put the total scripts tested in the graph
        plt.text(bar_pos[i], 102, str(totals[i]), ha='center', va='center', fontweight='bold')

        # Put the percentages in each box
        total = 0
        for j in range(4):
            if y[i][j] != 0:
                plt.text(bar_pos[i], (y[i][j] / 2) + total, f"{y[i][j]}%", ha='center', va='center')
            total += y[i][j]

    plt.legend()
    plt.savefig(outfile2)
    plt.show()