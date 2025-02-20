import os
import re
import git
import json
import time
from tqdm import tqdm
import requests
from requests.exceptions import RequestException
from openai import OpenAI
import difflib
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

UPDATE = True
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# OPENAI_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
pipeline_pattern = re.compile(
    r'^(?!\s*#).*?(?:(?<!\|)\|\s+\b(?:grep|awk|sed|cut|sort|uniq|tr|xargs|echo|cat|head|tail|wc|find|ls)\b)+'
)
# client = OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.deepseek.com")
client = OpenAI(api_key=OPENAI_API_KEY)

def normalize_line(line):
    # Remove the diff marker
    content = line[1:]
    # Remove any leading "command"
    content = re.sub(r'\bcommand\s+', '', content)
    # Remove any assignment
    content = re.sub(r'\b\w+\s*=\w+', '', content)
    content = re.sub(r'\b\w+\s*=\s+', '', content)
    # head/tail -n x -> head/tail -x
    content = re.sub(r'head\s+-n\s*(\d+)', r'head -\1', content)
    content = re.sub(r'tail\s+-n\s*(\d+)', r'tail -\1', content)
    # Remove any redirections
    content = re.sub(r'\S+>\s*\S+', '', content)
    content = re.sub(r'\S+>>\s*\S+', '', content)
    content = re.sub(r'\S+<\s*\S+', '', content)
    content = re.sub(r'\S+<<\s*\S+', '', content)
    # Remove any spaces
    content = re.sub(r'\s', '', content).strip()
    return content

def get_popular_repos(language="Shell", max_size_kb=150000, top_n=100, min_results=10):
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

    system_prompt = """Analyze the given commit to decide whether it fixes a bug specifically in the UNIX pipeline. A commit qualifies if it addresses an issue only related to the UNIX pipeline and the issue is self-contained within that pipeline context. In contrast, commits that change variables, perform general refactoring/simplification, or modify behaviors out of the pipeline context should be considered unqualified.
    
    There are some examples of unqualified commits:
    1.
    message: "fix(fossil): refactor `fossil_prompt_info` and quote % in branch"
    removed_lines: [
        "- local _BRANCH=`echo $_OUTPUT | grep \"* \" | sed 's/* //g'`"
    ]
    added_lines: [
        "+ local branch=$(echo $info | grep \"* \" | sed 's/* //g')"
    ]
    Reason: The change is a only a variable name change, so it is not within the UNIX pipeline context.

    2.
    message: "fix(installer): correct check for `sudo` in shell change logic"
    removed_lines: [
        "- LANG= sudo -n -v 2>&1 | grep -q \"may not run sudo\""
    ]
    added_lines: [
        "+ ! LANG= sudo -n -v 2>&1 | grep -q \"may not run sudo\""
    ]
    Reason: The change is not within the UNIX pipeline context.

    3.
    message: "fix(toolbox): avoid prompt injection",
    removed_lines: [
        "-  [[ -f /run/.containerenv ]] && cat /run/.containerenv | awk -F\\\" '/name/ { print$2 }'"
    ],
    added_lines: [
        "+  local _to_print=\"$(cat /run/.containerenv | awk -F\\\" '/name/ { print$2 }')\""
    ]
    Reason: The change is not within the UNIX pipeline context.

    If the commit is qualified according to these guidelines, respond with exactly: "True". Otherwise, respond with: "False". Do not include any additional output or explanation. For the above examples, the correct response would be: "False".
    """
    
    user_prompt = f"Commit message: {commit_data['message']}\n\nRemoved lines:\n{commit_data['removed_lines']}\n\n Added lines:\n{commit_data['added_lines']}"
    
    max_retries = 3
    delay_seconds = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                # model="deepseek-chat",
                # model="o3-mini",
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                timeout=10,
                stream=False,
                max_tokens=10,
                temperature=0,
                # reasoning_effort="low",
            )
            return "True" in response.choices[0].message.content
        except Exception as e:
            print(f"LLM call error on attempt {attempt} for commit {str(commit_data)}: {e}")
            if attempt < max_retries:
                time.sleep(delay_seconds)
    return False


def find_pipeline_commits(repo: git.Repo, github_url: str):
    pipeline_commits = []
    total_commits = int(repo.git.rev_list('--count', 'HEAD'))

    with tqdm(total=total_commits, desc="Processing commits") as pbar:
        for commit in repo.iter_commits():
            diff_data = commit.diff(commit.parents or None, create_patch=True)
            for diff in diff_data:
                if diff.b_path and diff.b_path.endswith(('.sh', '.bash', '.zsh')):
                    diff_text = diff.diff.decode('utf-8', errors='ignore')
                    
                    matched_lines = [line for line in diff_text.splitlines() if pipeline_pattern.search(line[1:])]
                    added_lines = [line for line in matched_lines if line.startswith('-')]
                    added_lines = list(map(lambda x: '+' + x[1:], added_lines))
                    removed_lines = [line for line in matched_lines if line.startswith('+')]
                    removed_lines = list(map(lambda x: '-' + x[1:], removed_lines))
                    SIMILARITY_THRESHOLD = 0.7

                    filtered_added = []
                    for a in added_lines:
                        if any(difflib.SequenceMatcher(None, a, r).ratio() >= SIMILARITY_THRESHOLD for r in removed_lines):
                            filtered_added.append(a)

                    filtered_removed = []
                    for r in removed_lines:
                        if any(difflib.SequenceMatcher(None, r, a).ratio() >= SIMILARITY_THRESHOLD for a in added_lines):
                            filtered_removed.append(r)

                    added_lines = filtered_added
                    removed_lines = filtered_removed

                    if removed_lines and added_lines:
                        if len(added_lines) + len(removed_lines) > 6:
                            print(f"Skipping commit {commit.hexsha} with {len(added_lines) + len(removed_lines)} lines of changes.")
                            continue

                        # Skip commit if the changes are trivial modifications
                        norm_added = [normalize_line(x) for x in added_lines]
                        norm_removed = [normalize_line(x) for x in removed_lines]
                        if norm_added and norm_removed and len(norm_added) == len(norm_removed) and sorted(norm_added) == sorted(norm_removed):
                            print(f"Skipping commit {commit.hexsha} due to trivial modification (simple addition/removal rules).")
                            continue

                        pipeline_commits.append({
                            "message": commit.message.strip(),
                            "commit_url": f"{github_url}/commit/{commit.hexsha}",
                            "removed_lines": removed_lines,
                            "added_lines": added_lines
                        })
                        break
            pbar.update(1)
            pbar.set_postfix(found=len(pipeline_commits))

    return pipeline_commits

def filter_commits_with_openai_analysis(commits, repo_name, save_path, max_workers=4):
    if OPENAI_API_KEY:
        filtered_commits = []
        commits_to_process = commits[:1000]
        total = len(commits_to_process)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_commit = {executor.submit(analyze_commit_with_openai, commit): commit for commit in commits_to_process}
            with tqdm(total=total, desc="Analyzing commits") as pbar:
                for future in as_completed(future_to_commit):
                    commit = future_to_commit[future]
                    try:
                        result = future.result()
                        if result:
                            filtered_commits.append(commit)
                    except Exception as e:
                        print(f"LLM analysis failed for commit {commit.get('commit_url', 'N/A')}: {e}")
                    pbar.update(1)
                    pbar.set_postfix(found=len(filtered_commits))
    else:
        print(f"Skipping LLM analysis for {repo_name} (no API key provided).")
        filtered_commits = commits

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump({repo_name: filtered_commits}, f, ensure_ascii=False, indent=4)
    print(f"Filtered results saved to {save_path}.")
    return filtered_commits

def load_existing_results(results_path, repo_name):
    save_path = os.path.join(results_path, f"{repo_name.replace('/', '_')}_pipeline_commits.json")
    openai_save_path = os.path.join(results_path, f"{repo_name.replace('/', '_')}_filtered_commits.json")
    
    commits = None
    filtered_commits = None
    
    if os.path.exists(save_path):
        with open(save_path, "r", encoding="utf-8") as f:
            commits = json.load(f)[repo_name]
    
    if os.path.exists(openai_save_path):
        with open(openai_save_path, "r", encoding="utf-8") as f:
            filtered_commits = json.load(f)[repo_name]
            
    return commits, filtered_commits

def save_summary(results_path, summary_data):
    commits_array = []
    
    for repo_name, repo_data in summary_data.items():
        if repo_data.get("commits"):
            for commit in repo_data["commits"]:
                commit_copy = commit.copy()
                commit_copy["repo"] = repo_name
                commit_copy["category"] = ""
                commit_copy["notes"] = ""
                commits_array.append(commit_copy)
    
    summary_path = os.path.join(results_path, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(commits_array, f, ensure_ascii=False, indent=4)
    print(f"Summary saved to {summary_path}")

def main(commit_limit, workers):
    repos = get_popular_repos()
    base_path = os.path.dirname(os.path.abspath(__file__)) + "/repos"
    results_path = os.path.dirname(os.path.abspath(__file__)) + "/results"
    os.makedirs(base_path, exist_ok=True)
    os.makedirs(results_path, exist_ok=True)
    
    summary = {}
    total_commits_collected = 0

    for repo_info in repos:
        repo_name = repo_info["full_name"]
        repo_url = repo_info["html_url"]
        local_path = os.path.join(base_path, repo_name.replace("/", "_"))
        save_path = os.path.join(results_path, f"{repo_name.replace('/', '_')}_pipeline_commits.json")
        openai_save_path = os.path.join(results_path, f"{repo_name.replace('/', '_')}_filtered_commits.json")

        if not UPDATE and os.path.exists(save_path) and os.path.exists(openai_save_path):
            print(f"Loading existing results for {repo_name}...")
            commits, filtered_commits = load_existing_results(results_path, repo_name)
        else:
            print(f"\nProcessing repository: {repo_name}...")
            clone_repo(repo_url, local_path)
            repo = git.Repo(local_path)
            commits = find_pipeline_commits(repo, repo_url)

            if commits:
                print(f"Found {len(commits)} commits with pipeline changes in {repo_name}.")
                filtered_commits = filter_commits_with_openai_analysis(commits, repo_name, openai_save_path, max_workers=workers)
                
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump({repo_name: commits}, f, ensure_ascii=False, indent=4)
                print(f"\nResults saved to {save_path}.")
            else:
                print(f"No pipeline changes found in {repo_name}.")
                commits = []
                filtered_commits = []

        if commits is not None:
            summary[repo_name] = {
                "total_commits": len(commits),
                "filtered_commits": len(filtered_commits) if filtered_commits else 0,
                "commits": commits,
                "filtered_commits_data": filtered_commits
            }
            total_commits_collected += len(commits)
        
        if total_commits_collected >= commit_limit:
            print(f"Commit limit reached: {total_commits_collected} commits collected, limit is {commit_limit}. Stopping further repo processing.")
            break
    
    save_summary(results_path, summary)

def parse_args():
    parser = argparse.ArgumentParser(description="Collect pipeline commits from popular repositories")
    parser.add_argument('--workers', type=int, default=6, help='Number of parallel threads to use for LLM analysis')
    parser.add_argument('--commit_limit', type=int, default=1000, help='Total commit limit across repositories')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    main(commit_limit=args.commit_limit, workers=args.workers)
