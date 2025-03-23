import json
import csv
import os

def main():
    evaluation_result_file = "./evaluation_results/with_annotations/evaluation_results.json"

    with open(evaluation_result_file, 'r') as f:
        data = json.load(f)
    
    automata_sizes = []
    
    for result in data.get('evaluation_results', []):
        automata_size = result.get('automata_size')
        if automata_size is not None:
            automata_sizes.append(automata_size)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "automata_size.csv")
    
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['automata_size'])
        for size in automata_sizes:
            writer.writerow([size])

if __name__ == "__main__":
    main()
