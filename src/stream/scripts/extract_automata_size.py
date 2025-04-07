import json
import csv
import os

def main():
    evaluation_result_file = "./evaluation_results/ann:y_heuristic:y/evaluation_results.json"

    with open(evaluation_result_file, 'r') as f:
        data = json.load(f)
    
    automata_sizes = []
    
    for result in data.get('evaluation_results', []):
        automata_size = result.get('automata_size')
        if automata_size is not None:
            automata_sizes.append(automata_size)
    
    csv_path = "evaluation_results/ann:y_heuristic:y/automata_sizes.csv"
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['automata_size'])
        for size in automata_sizes:
            writer.writerow([size])

if __name__ == "__main__":
    main()
