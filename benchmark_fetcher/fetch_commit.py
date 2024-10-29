import os
import re
import git
import json
from tqdm import tqdm
import requests
from requests.exceptions import RequestException
from openai import OpenAI

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
pipeline_pattern = re.compile(r'(\bgrep\b|\bawk\b|\bsed\b|\bcut\b|\bsort\b|\buniq\b|\btr\b|\bxargs\b|\becho\b|\bcat\b).*\|\s*')
debug_commit_hash = "6f994715d6e86297d1c9851666221cd2eb09ac3c"

def get_popular_repos(language="Shell", max_size_kb=5000, top_n=50, min_results=15):
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable not set.")
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = "https://api.github.com/search/repositories"
    params = {
        "q": f"language:{language}",
        "sort": "stars",
        "order": "desc",
        "per_page": top_n,
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        repos = response.json().get("items", [])
        
        filtered_repos = [repo for repo in repos if repo["size"] <= max_size_kb]
        if len(filtered_repos) < min_results:
            print(f"Warning: Only found {len(filtered_repos)} repos, fewer than minimum required {min_results}.")
        
        return filtered_repos[:min_results]
    except RequestException as e:
        print(f"Error fetching popular repos: {e}")
        return []

def clone_repo(github_url: str, local_path: str):
    try:
        if not os.path.exists(local_path):
            print(f"Cloning repository from {github_url} to {local_path}...")
            git.Repo.clone_from(github_url, local_path)
        else:
            print(f"Repository already exists at {local_path}.")
    except git.exc.GitCommandError as e:
        print(f"Error cloning repo {github_url}: {e}")

def analyze_commit_with_openai(commit_data):
    if not OPENAI_API_KEY:
        return True

    client = OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.deepseek.com")

    system_prompt = """Analyze each commit to determine if it modifies at least one pipeline by adding, removing, or changing flags, options, or arguments. Ignore changes irrelevant to the pipeline or changes to the commands themselves. Respond with 'T' if the commit meets the criteria; otherwise, respond with 'F'.

    Examples:
    - `grep -oE [0-9]+ | sort` to `grep -oE [0-9]+ | sort -n` → 'T' (flag added)
    - `grep -oE [0-9]+ | sort` to `grep -oE [0-9]+ | uniq` → 'F' (command changed)
    - `grep -oE [0-9A-Z]+ | sort -n` to `grep -oE [0-9A-Z]+` → 'F' (command dropped)
    - `grep -oE [0-9]+ | sort` to `grep -oE [0-9]+ | sort | uniq` → 'F' (command added)"""


    user_prompt = f"Commit message: {commit_data['message']}\n\nRemoved lines:\n{commit_data['removed_lines']}\n\n Added lines:\n{commit_data['added_lines']}"
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=False,
        max_tokens=2,
        temperature=0
    )
    return "T" in response.choices[0].message.content

def find_pipeline_commits(repo: git.Repo, github_url: str):
    pipeline_commits = []
    total_commits = int(repo.git.rev_list('--count', 'HEAD'))

    with tqdm(total=total_commits, desc="Processing commits") as pbar:
        for commit in repo.iter_commits():
            if debug_commit_hash and commit.hexsha == debug_commit_hash:
                print("="*60)
                print(f"Processing debug commit: {debug_commit_hash}")
                print(f"Author: {commit.author.name}")
                print(f"Message: {commit.message.strip()}")
            diff_data = commit.diff(commit.parents or None, create_patch=True)
            for diff in diff_data:
                if diff.b_path and diff.b_path.endswith(('.sh', '.bash', '.zsh')):
                    diff_text = diff.diff.decode('utf-8', errors='ignore')
                    
                    removed_lines = [line for line in diff_text.splitlines() if line.startswith('-') and pipeline_pattern.search(line)]
                    added_lines = [line for line in diff_text.splitlines() if line.startswith('+') and pipeline_pattern.search(line)]

                    if removed_lines and added_lines:
                        if debug_commit_hash and commit.hexsha == debug_commit_hash:
                            print(f"\nMatch found in debug commit {debug_commit_hash}")
                            print("Removed lines:\n" + "\n".join(removed_lines))
                            print("Added lines:\n" + "\n".join(added_lines))
                            print("="*60)

                        pipeline_commits.append({
                            "commit_hash": commit.hexsha,
                            "author": commit.author.name,
                            "message": commit.message.strip(),
                            "commit_url": f"{github_url}/commit/{commit.hexsha}",
                            "removed_lines": removed_lines,
                            "added_lines": added_lines
                        })
                        break
            pbar.update(1)
            pbar.set_postfix(found=len(pipeline_commits))

    return pipeline_commits

def filter_commits_with_openai_analysis(commits, repo_name, save_path):
    if OPENAI_API_KEY:
        filtered_commits = []
        with tqdm(total=len(commits[:200]), desc="OpenAI Analysis Progress") as pbar:
            for commit in commits[:200]:
                if analyze_commit_with_openai(commit):
                    filtered_commits.append(commit)
                pbar.update(1)
                pbar.set_postfix(found=len(filtered_commits))
    else:
        print(f"Skipping OpenAI analysis for {repo_name} (no API key provided).")
        filtered_commits = commits

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump({repo_name: filtered_commits}, f, ensure_ascii=False, indent=4)
    print(f"Filtered results saved to {save_path}.")

def main():
    repos = get_popular_repos()
    base_path = "./benchmark_fetcher/repos"
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    results = {}

    for repo_info in repos:
        repo_name = repo_info["full_name"]
        repo_url = repo_info["html_url"]
        local_path = os.path.join(base_path, repo_name.replace("/", "_"))
        save_path = f"./benchmark_fetcher/results/{repo_name.replace('/', '_')}_pipeline_commits.json"
        openai_save_path = f"./benchmark_fetcher/results/{repo_name.replace('/', '_')}_filtered_commits.json"

        print(f"\nProcessing repository: {repo_name}...")

        clone_repo(repo_url, local_path)

        repo = git.Repo(local_path)
        commits = find_pipeline_commits(repo, repo_url)

        if commits:
            results[repo_name] = commits
            print(f"Found {len(commits)} commits with pipeline changes in {repo_name}.")

            filter_commits_with_openai_analysis(commits, repo_name, openai_save_path)
            
        else:
            print(f"No pipeline changes found in {repo_name}.")

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump({repo_name: commits}, f, ensure_ascii=False, indent=4)
        print(f"\nResults saved to {save_path}.")

if __name__ == "__main__":
    main()
