import json
import os
import re
import git
import difflib
from tqdm import tqdm

def parse_commit_url(commit_url):
    pattern = re.compile(r'https://github.com/([^/]+)/([^/]+)/commit/([0-9a-f]+)')
    match = pattern.match(commit_url)
    return match.groups() if match else (None, None, None)

def clone_repository(repo_url, local_path):
    try:
        if not os.path.exists(local_path):
            print(f"Cloning {repo_url} to {local_path}...")
            git.Repo.clone_from(repo_url, local_path)
        return git.Repo(local_path)
    except git.exc.GitCommandError as e:
        print(f"Clone failed: {e}")
        return None

def get_commit_diff(repo, commit_hash, commit_url):
    try:
        commit = repo.commit(commit_hash)
        return commit.parents[0].diff(commit, create_patch=True) if commit.parents else commit.diff(None, create_patch=True)
    except git.exc.BadName:
        print(f"Warning: Commit not found: {commit_url}")
        return None

def parse_diff_hunk_header(header_line):
    match = re.match(r"@@ \-(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", header_line)
    if not match:
        return None
    old_start = int(match.group(1))
    old_len = int(match.group(2) or 1)
    new_start = int(match.group(3))
    new_len = int(match.group(4) or 1)
    return (old_start, old_len, new_start, new_len)

def pair_pipelines(removed, added):
    pairs = []
    used_added = set()
    for r in removed:
        best_similarity = 0
        best_a = None
        best_index = None
        for i, a in enumerate(added):
            if i in used_added:
                continue
            sim = difflib.SequenceMatcher(None, r, a).ratio()
            if sim > best_similarity:
                best_similarity = sim
                best_a = a
                best_index = i
        if best_a is not None:
            pairs.append((r, best_a))
            used_added.add(best_index)
    return pairs

def build_group_header(group, record):
    removed_group = [line for (line, t, idx) in group if t == '-']
    added_group = [line for (line, t, idx) in group if t == '+']
    header_block = []
    header_block.append("#" * 80)
    message = record['message'].replace('\n', ' ')
    header_block.append(f"# Commit message: {message}")
    header_block.append(f"# Commit URL: {record['commit_url']}")
    header_block.append(f"# Category: {record['category']}")
    header_block.append(f"# Notes: {record['notes']}")
    header_block.append("# Changed content:")
    if removed_group and added_group:
        pairs = pair_pipelines(removed_group, added_group)
        for r, a in pairs:
            header_block.append("# - " + r.lstrip('-').strip())
            header_block.append("# + " + a.lstrip('+').strip())
    else:
        for r in removed_group:
            header_block.append("# - " + r.lstrip('-').strip())
        for a in added_group:
            header_block.append("# + " + a.lstrip('+').strip())
    header_block.append("#" * 80)
    header_block.extend(["# put stream annotation here", "# stream enable"])
    return header_block, len(removed_group), len(added_group)

def process_diff(diff, record):
    old_path = diff.a_blob.path if diff.a_blob else None
    new_path = diff.b_blob.path if diff.b_blob else None
    file_path = old_path or new_path

    if not file_path or not any(file_path.endswith(ext) for ext in ('.sh', '.bash', '.zsh')):
        return None

    old_content = []
    if diff.a_blob and diff.change_type != 'A':
        try:
            old_content = diff.a_blob.data_stream.read().decode('utf-8', errors='ignore').splitlines()
        except Exception as e:
            print(f"Error reading old blob: {e}")
            return None

    new_content = []
    if diff.b_blob and diff.change_type != 'D':
        try:
            new_content = diff.b_blob.data_stream.read().decode('utf-8', errors='ignore').splitlines()
        except Exception as e:
            print(f"Error reading new blob: {e}")
            return None

    try:
        diff_text = diff.diff.decode('utf-8', errors='ignore').splitlines()
    except Exception as e:
        print(f"Error decoding diff: {e}")
        return None

    old_line_num = None
    new_line_num = None
    old_offset = 0
    new_offset = 0
    header_injected = False

    group = []

    def flush_group():
        nonlocal old_offset, new_offset, header_injected, group, old_content, new_content
        if not group:
            return
        header_block, count_removed, count_added = build_group_header(group, record)
        if count_removed > 0:
            idx = min(item[2] for item in group if item[1] == '-')
            for h in header_block:
                old_content.insert(idx, h)
                idx += 1
            old_offset += len(header_block)
        if count_added > 0:
            idx = min(item[2] for item in group if item[1] == '+')
            for h in header_block:
                new_content.insert(idx, h)
                idx += 1
            new_offset += len(header_block)
        header_injected = True
        group = []

    for line in diff_text:
        if line.startswith(('diff --git', 'index', '---', '+++')):
            continue
        if line.startswith('@@'):
            flush_group()
            parsed = parse_diff_hunk_header(line)
            if parsed:
                old_line_num, _, new_line_num, _ = parsed
            continue
        if line.startswith(' '):
            flush_group()
            old_line_num += 1
            new_line_num += 1
            continue
        # Changed lines.
        if line.startswith('-'):
            if line in record.get('removed_lines', []):
                insertion_index = old_line_num - 1 + old_offset
                group.append((line, '-', insertion_index))
            old_line_num += 1
            continue
        if line.startswith('+'):
            if line in record.get('added_lines', []):
                insertion_index = new_line_num - 1 + new_offset
                group.append((line, '+', insertion_index))
            new_line_num += 1
            continue

    flush_group()

    if not header_injected:
        return None

    return {
        'file_path': file_path,
        'old_content': old_content,
        'new_content': new_content,
        'change_type': diff.change_type
    }

def save_versioned_files(record, file_data, output_dir):
    commit_hash = parse_commit_url(record['commit_url'])[2]
    base_name = os.path.basename(file_data['file_path'])
    
    pre_dir = os.path.join(output_dir, 'pre_commit')
    post_dir = os.path.join(output_dir, 'post_commit')
    os.makedirs(pre_dir, exist_ok=True)
    os.makedirs(post_dir, exist_ok=True)

    file_name = (
        file_data['file_path'].replace('/', '_') +
        "_" + ".".join(base_name.split('.')[:-1]) +
        "_" + commit_hash[:7] +
        "." + base_name.split('.')[-1]
    )

    if file_data['change_type'] != 'A':
        pre_file_path = os.path.join(pre_dir, file_name)
        with open(pre_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(file_data['old_content']))
    
    if file_data['change_type'] != 'D':
        post_file_path = os.path.join(post_dir, file_name)
        with open(post_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(file_data['new_content']))

def process_json_records(input_json, output_dir):
    with open(input_json, 'r', encoding='utf-8') as f:
        records = [r for r in json.load(f)]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    for record in tqdm(records, desc="Processing commits"):
        owner, repo_name, commit_hash = parse_commit_url(record['commit_url'])
        if not owner:
            continue

        repo_path = os.path.join(base_dir, "repos", repo_name)
        repo = clone_repository(f"https://github.com/{owner}/{repo_name}.git", repo_path)
        if not repo:
            continue

        diffs = get_commit_diff(repo, commit_hash, record['commit_url'])
        if diffs is None:
            continue

        for diff in diffs:
            file_data = process_diff(diff, record)
            if file_data:
                save_versioned_files(record, file_data, output_dir)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(base_dir, "repos"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "output_new"), exist_ok=True)
    process_json_records(
        os.path.join(base_dir, "results/summary.json"),
        os.path.join(base_dir, "output_new")
    )
