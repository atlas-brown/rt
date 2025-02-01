import json
import os
import re
import git
from tqdm import tqdm

def parse_commit_url(commit_url):
    """Parse GitHub commit URL to extract owner, repo, and commit hash."""
    pattern = re.compile(r'https://github.com/([^/]+)/([^/]+)/commit/([0-9a-f]+)')
    match = pattern.match(commit_url)
    return match.groups() if match else (None, None, None)

def clone_repository(repo_url, local_path):
    """Clone repository if not exists locally."""
    try:
        if not os.path.exists(local_path):
            print(f"Cloning {repo_url} to {local_path}...")
            git.Repo.clone_from(repo_url, local_path)
        return git.Repo(local_path)
    except git.exc.GitCommandError as e:
        print(f"Clone failed: {e}")
        return None

def get_commit_diff(repo, commit_hash):
    """Retrieve diff for a specific commit."""
    try:
        commit = repo.commit(commit_hash)
        # If there are parent commits, diff with the first parent; otherwise, diff with nothing.
        return commit.parents[0].diff(commit, create_patch=True) if commit.parents else commit.diff(None, create_patch=True)
    except git.exc.BadName:
        print(f"Commit not found: {commit_hash}")
        return []

def parse_diff_hunk_header(header_line):
    """Parse diff hunk header to get starting line numbers and lengths.
    
    Returns a tuple (old_start, old_len, new_start, new_len) or None if no match.
    """
    match = re.match(r"@@ \-(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", header_line)
    if not match:
        return None
    old_start = int(match.group(1))
    old_len = int(match.group(2) or 1)
    new_start = int(match.group(3))
    new_len = int(match.group(4) or 1)
    return (old_start, old_len, new_start, new_len)

def process_diff(diff, record):
    """Process diff manually and insert annotation headers into the file contents.
    
    This function uses a per-hunk approach. For each hunk header, we initialize
    counters for old and new line numbers. Changed lines are now grouped by type:
    removed and added lines are accumulated in separate groups. When a flush is triggered
    (by a context line or a new hunk header), if any of the changed lines involves a Unix pipeline,
    a header is constructed showing both the removed (prefixed with "# -") and the added 
    (prefixed with "# +") lines. This header is then inserted into both the pre–commit and post–commit 
    versions.
    
    Additionally, the cumulative offsets (old_offset/new_offset) are no longer reset per hunk,
    ensuring that if a file contains multiple hunks with header insertions, later hunks
    are inserted at the correct line number.
    """
    # Check if blobs are text files. Instead of relying on mime_type (which might not be set),
    # we simply continue if the file extension is not one of the allowed ones.
    old_path = diff.a_blob.path if diff.a_blob else None
    new_path = diff.b_blob.path if diff.b_blob else None
    file_path = old_path or new_path

    if not file_path or not any(file_path.endswith(ext) for ext in ('.sh', '.bash', '.zsh')):
        return None

    # Read original file contents from blobs if applicable.
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

    # Split the diff text into lines.
    try:
        diff_text = diff.diff.decode('utf-8', errors='ignore').splitlines()
    except Exception as e:
        print(f"Error decoding diff: {e}")
        return None

    # Variables for tracking hunk positions and header offsets.
    old_line_num = None
    new_line_num = None
    old_offset = 0
    new_offset = 0

    # Instead of one group variable we now track two groups:
    removed_group = None  # dict with keys: 'start' and 'lines' for removed lines
    added_group = None    # dict with keys: 'start' and 'lines' for added lines

    # Flush the current groups: insert header into both file contents.
    def flush_groups():
        nonlocal removed_group, added_group, old_offset, new_offset
        if removed_group is None and added_group is None:
            return
        # Combine changed lines from both groups.
        combined_lines = []
        if removed_group is not None:
            combined_lines.extend(removed_group['lines'])
        if added_group is not None:
            combined_lines.extend(added_group['lines'])
        # Check if the changed lines involve a Unix pipeline.
        if not any(re.search(r'\|', line) or line.rstrip().endswith('|') for line in combined_lines):
            removed_group = None
            added_group = None
            return
        header = []
        header.append("#" * 80)
        message = record['message'].replace('\n', ' ')
        header.append(f"# Commit message: {message}")
        header.append(f"# Commit URL: {record['commit_url']}")
        header.append(f"# Category: {record['category']}")
        header.append(f"# Notes: {record['notes']}")
        header.append("# Changed content:")
        if removed_group is not None:
            for line in removed_group['lines']:
                content = line[1:] if line.startswith('-') else line
                header.append("# - " + content)
        if added_group is not None:
            for line in added_group['lines']:
                content = line[1:] if line.startswith('+') else line
                header.append("# + " + content)
        header.append("#" * 80)
        header.append("# put stream annotation here")
        header.append("# stream enable")
        # Determine insertion positions:
        # For old_content, if removed_group exists, use its start; otherwise use added_group's start.
        if removed_group is not None:
            old_insertion = removed_group['start'] - 1 + old_offset
        else:
            old_insertion = added_group['start'] - 1 + old_offset
        # For new_content, if added_group exists, use its start; otherwise use removed_group's start.
        if added_group is not None:
            new_insertion = added_group['start'] - 1 + new_offset
        else:
            new_insertion = removed_group['start'] - 1 + new_offset
        for h_line in header:
            old_content.insert(old_insertion, h_line)
            old_insertion += 1
        old_offset += len(header)
        for h_line in header:
            new_content.insert(new_insertion, h_line)
            new_insertion += 1
        new_offset += len(header)
        removed_group = None
        added_group = None

    # Iterate through each line in the diff text.
    for line in diff_text:
        # Skip non-diff lines.
        if line.startswith(('diff --git', 'index', '---', '+++')):
            flush_groups()
            continue

        # Check for a new hunk header.
        if line.startswith('@@'):
            flush_groups()
            parsed = parse_diff_hunk_header(line)
            if parsed:
                old_line_num, _, new_line_num, _ = parsed
                # *** FIX 1: Do not reset the cumulative offsets here ***
                # (old_offset and new_offset are left unchanged across hunks)
            continue

        # If we haven't encountered a hunk header, skip.
        if old_line_num is None or new_line_num is None:
            continue

        # For context lines, flush any current groups and increment both counters.
        if line.startswith(' '):
            flush_groups()
            old_line_num += 1
            new_line_num += 1
        # For removed lines.
        elif line.startswith('-'):
            if removed_group is None:
                removed_group = {'start': old_line_num, 'lines': []}
            removed_group['lines'].append(line)
            old_line_num += 1
        # For added lines.
        elif line.startswith('+'):
            if added_group is None:
                added_group = {'start': new_line_num, 'lines': []}
            added_group['lines'].append(line)
            new_line_num += 1
        else:
            flush_groups()

    # Flush any groups remaining at the end of the diff.
    flush_groups()

    return {
        'file_path': file_path,
        'old_content': old_content,
        'new_content': new_content,
        'change_type': diff.change_type
    }

def save_versioned_files(record, file_data, output_dir):
    """Save annotated files to versioned directories."""
    commit_hash = parse_commit_url(record['commit_url'])[2]
    base_name = os.path.basename(file_data['file_path'])
    
    # Create version directories.
    pre_dir = os.path.join(output_dir, 'pre_commit')
    post_dir = os.path.join(output_dir, 'post_commit')
    os.makedirs(pre_dir, exist_ok=True)
    os.makedirs(post_dir, exist_ok=True)

    file_name = file_data['file_path'].replace('/', '_') + "_" + ".".join(base_name.split('.')[:-1]) + "_" + commit_hash[:7] + "." + base_name.split('.')[-1]

    # Save pre-commit version if the file is not newly added.
    if file_data['change_type'] != 'A':
        pre_file_path = os.path.join(pre_dir, file_name)
        with open(pre_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(file_data['old_content']))
    
    # Save post-commit version if the file is not deleted.
    if file_data['change_type'] != 'D':
        post_file_path = os.path.join(post_dir, file_name)
        with open(post_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(file_data['new_content']))

def process_json_records(input_json, output_dir):
    """Main processing function for JSON records."""
    with open(input_json, 'r', encoding='utf-8') as f:
        # Only process records that have a 'category' field.
        records = [r for r in json.load(f) if r.get('category')]

    for record in tqdm(records, desc="Processing commits"):
        owner, repo_name, commit_hash = parse_commit_url(record['commit_url'])
        if not owner:
            continue

        repo = clone_repository(f"https://github.com/{owner}/{repo_name}.git", 
                                os.path.join("repos", repo_name))
        if not repo:
            continue

        for diff in get_commit_diff(repo, commit_hash):
            file_data = process_diff(diff, record)
            if file_data:
                save_versioned_files(record, file_data, output_dir)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(base_dir, "repos"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "output"), exist_ok=True)
    process_json_records(
        os.path.join(base_dir, "results/summary_241112.json"),
        os.path.join(base_dir, "output")
    )
