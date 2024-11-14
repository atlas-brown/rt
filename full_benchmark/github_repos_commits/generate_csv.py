import json
from collections import Counter
import os

root = os.path.dirname(os.path.abspath(__file__))

def analyze_commits(data):
    categories = [commit['category'] for commit in data if commit['category']]
    
    category_counts = Counter(categories)
    with open(root + '/category_counts.csv', 'w') as f:
        print("Category, Count")
        f.write("Category, Count\n")
        for category, count in category_counts.items():
            print(f"{category}, {count}")
            f.write(f"{category}, {count}\n")

if __name__ == "__main__":
    with open(root + '/results/summary_241112.json', 'r') as f:
        data = json.load(f)
    
    analyze_commits(data)