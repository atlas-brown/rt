import os
import json

def contains_pipe(text):
    return '|' in text

def load_and_extract(directory, save_path):
    json_contents = []

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as file:
                try:
                    data = json.load(file)
                    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                        json_contents.extend(data)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from file {filename}")

    for idx, item in enumerate(json_contents):
        query = item.get('query')
        gold = item.get('gold')
        gold2 = item.get('gold2')

        if contains_pipe(gold):
            gold1_content = f"# Query: {query}\n\n{gold}"
            with open(f"{save_path}/intercode_{idx+1}_gold1.sh", 'w') as f:
                f.write(gold1_content)

        if contains_pipe(gold2):
            gold2_content = f"# Query: {query}\n\n{gold2}"
            with open(f"{save_path}/intercode_{idx+1}_gold2.sh", 'w') as f:
                f.write(gold2_content)

def main():
    directory_path = os.path.dirname(os.path.abspath(__file__)) + '/InterCode-ALFA-Data'
    save_path = os.path.dirname(os.path.abspath(__file__)) + '/pipelines'
    os.makedirs(save_path, exist_ok=True)
    load_and_extract(directory_path, save_path)

if __name__ == "__main__":
    main()
