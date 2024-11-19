import json

path = './evaluation_results/evaluation_results.json'
outpath = './evaluation_results/results.csv'

def split_id_into_name_and_collection(id):
    path, index = id
    parts = path.split('/')
    name = parts[3:] + [str(index)]
    collection = parts[:3]
    return '/'.join(name), '/'.join(collection)

def gen_reason(result):
    if result["tool runtime error"]:
        return f"crash: {result['tool runtime error']}"
    elif result["category"] != "<missing>":
        return result["category"]
    else:
        return ""

def results_to_summary_csv(json_path, out_path):
    with open(json_path, 'r') as f:
        results = json.load(f)["evaluation_results"]
    results.sort(key=lambda x: x["id"])
    with open(out_path, 'w') as f:
        f.write('Benchmark,Collection,Buggy?,CorrectResult?,Time(s),Reason,Notes,Pipeline\n')
        for result in results:
            name, collection = split_id_into_name_and_collection(result["id"])
            f.write(f'{name},{collection},{result["is buggy?"]},{result["warning signaled?"] == result["is buggy?"]},{result["evaluation_time"]},{gen_reason(result)},{result["notes"]},{result["content"]}\n')

if __name__ == '__main__':
    results_to_summary_csv(path, outpath)


