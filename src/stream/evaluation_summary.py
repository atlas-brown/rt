import json

path = './evaluation_results/evaluation_results.json'
outpath = './evaluation_results/results.csv'

def split_id_into_name_and_collection(address):
    parts = address.split('/')
    name = parts[-1]
    collection = '/'.join(parts[:-1])
    return name, collection

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
            name, collection = split_id_into_name_and_collection(result["address"])
            f.write(f'{name},{collection},{result["is buggy?"]},{result["warning signaled?"] == result["is buggy?"]},{result["evaluation_time"]},{process_runtime_error(result["tool runtime error"])},{process_category(result["category"])}, {result["notes"]},{process_content(result["content"])}\n')

if __name__ == '__main__':
    results_to_summary_csv(path, outpath)


