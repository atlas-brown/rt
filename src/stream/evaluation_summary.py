import argparse
import json

def convert_to_github_address(address):
    parts = address.split('/')
    collection = '/'.join(parts[:-1])
    if address.startswith('./'):
        address = address[2:]
    address = "https://github.com/brown-cs2952r/StreamTypes/blob/main/" + address
    return address, collection

def process_runtime_error(error):
    if error is None:
        return ''
    return error


def process_category(category):
    if category is None or category == '<missing>':
        return ''
    return category

def process_content(content):
    if content is None:
        return ''
    s = content.replace('\n', ' ')
    if (len(s) > 300):
        s = s[:300] + '...'
    return s

def results_to_summary_csv(json_path, out_path):
    with open(json_path, 'r') as f:
        results = json.load(f)["evaluation_results"]
    results.sort(key=lambda x: x["address"])
    with open(out_path, 'w') as f:
        f.write('Benchmark,Collection,Buggy?,Correct Result?,Time(s),RunTime Error,Category,Notes,Pipeline\n')
        for result in results:
            name, collection = convert_to_github_address(result["address"])
            f.write(f'{name},{collection},{result["is buggy?"]},{result["warning signaled?"] == result["is buggy?"]},{result["evaluation_time"]},{process_runtime_error(result["tool runtime error"])},{process_category(result["category"])}, {result["notes"]},{process_content(result["content"])}\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process evaluation results from JSON file and generate a CSV summary.')
    parser.add_argument('--path', type=str, default='./evaluation_results/evaluation_results.json',
                        help='Input JSON path (default: ./evaluation_results/evaluation_results.json)')
    parser.add_argument('--outpath', type=str, default='./evaluation_results/results.csv',
                        help='Output CSV file path (default: ./evaluation_results/results.csv)')
    
    args = parser.parse_args()
    
    results_to_summary_csv(args.path, args.outpath)


