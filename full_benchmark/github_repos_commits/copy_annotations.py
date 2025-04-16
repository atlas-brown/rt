import os
import re
from tqdm import tqdm
import sys

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Adjust these paths if the script is not in the parent dir of pre/post_commit
PRE_COMMIT_DIR = os.path.join(SCRIPT_DIR, "collected/pre_commit")
POST_COMMIT_DIR = os.path.join(SCRIPT_DIR, "collected/post_commit")

HEADER_START_PATTERN = r"^#{80}$"  # Match exactly 80 '#' characters at the start of a line
HEADER_END_MARKER = "# stream enable"
# --- End Configuration ---

def find_all_header_blocks(lines):
    """
    Finds all header blocks (from '#####' to '# stream enable') in a list of lines.

    Args:
        lines (list): A list of strings representing the lines of a file (with trailing newlines).

    Returns:
        list: A list of tuples. Each tuple contains:
              (header_lines (list), start_index (int), end_index (int)).
              Returns an empty list if no blocks are found.
    """
    found_blocks = []
    in_header = False
    current_header_lines = []
    start_index = -1

    for i, line in enumerate(lines):
        # Using strip() for marker checks but storing original lines
        line_stripped = line.strip()

        if not in_header and re.match(HEADER_START_PATTERN, line_stripped):
            # Start of a new header block
            in_header = True
            start_index = i
            current_header_lines = [line] # Store original line
        elif in_header:
            # Inside a header block, keep collecting lines
            current_header_lines.append(line) # Store original line
            if line_stripped == HEADER_END_MARKER:
                # End of the current header block
                found_blocks.append((current_header_lines, start_index, i))
                # Reset for potentially finding the next block
                in_header = False
                current_header_lines = []
                start_index = -1
        # If line doesn't match start/end and we are not in header, do nothing.

    # Note: If the file ends while inside a header block without an end marker,
    # that partial block is ignored by this logic.

    return found_blocks

def synchronize_headers(pre_dir, post_dir):
    """
    Synchronizes potentially multiple headers from pre-commit files to post-commit files.
    Matches headers positionally (1st pre -> 1st post, 2nd pre -> 2nd post, etc.).
    """
    print(f"Scanning pre-commit directory: {pre_dir}")
    if not os.path.isdir(pre_dir):
        print(f"Error: Pre-commit directory not found: {pre_dir}")
        return

    print(f"Target post-commit directory: {post_dir}")
    if not os.path.isdir(post_dir):
        print(f"Error: Post-commit directory not found: {post_dir}")
        return

    pre_commit_files = [
        f for f in os.listdir(pre_dir)
        if os.path.isfile(os.path.join(pre_dir, f)) and any(f.endswith(ext) for ext in ('.sh', '.bash', '.zsh'))
    ]

    print(f"Found {len(pre_commit_files)} potential shell script files in {pre_dir}.")
    synced_files_count = 0
    skipped_files_count = 0
    error_files_count = 0
    total_headers_synced = 0

    for filename in tqdm(pre_commit_files, desc="Synchronizing Headers"):
        pre_commit_path = os.path.join(pre_dir, filename)
        post_commit_path = os.path.join(post_dir, filename)
        processed_file = False # Flag to track if sync occurred for this file

        if not os.path.exists(post_commit_path):
            # print(f"Skipping: Post-commit file not found for {filename}")
            skipped_files_count += 1
            continue

        try:
            # 1. Read pre-commit file and find all *new* header blocks
            with open(pre_commit_path, 'r', encoding='utf-8', errors='ignore') as f_pre:
                pre_lines = f_pre.readlines() # Keep trailing newlines
            pre_headers = find_all_header_blocks(pre_lines)

            if not pre_headers:
                # print(f"Skipping: No header blocks found in {pre_commit_path}")
                skipped_files_count += 1
                continue # Nothing to sync from pre-commit file

            # 2. Read post-commit file and find all *old* header blocks
            with open(post_commit_path, 'r', encoding='utf-8', errors='ignore') as f_post:
                post_lines_original = f_post.readlines() # Keep trailing newlines
            post_headers = find_all_header_blocks(post_lines_original)

            if not post_headers:
                # print(f"Skipping: No header blocks found in {post_commit_path} to replace.")
                skipped_files_count += 1
                continue # Nothing to replace in post-commit file

            # 3. Determine how many headers to replace (minimum of counts found)
            num_to_replace = min(len(pre_headers), len(post_headers))
            if len(pre_headers) != len(post_headers):
                print(f"\nWarning: Mismatched header count in {filename}. "
                      f"Pre: {len(pre_headers)}, Post: {len(post_headers)}. "
                      f"Replacing first {num_to_replace}.")

            if num_to_replace == 0:
                skipped_files_count += 1
                continue # Should be covered by earlier checks, but good safeguard

            # 4. Construct the new content for the post-commit file
            # Strategy: Build the new list segment by segment
            new_post_lines = []
            last_copied_post_index = -1 # Index *after* the last character copied from original

            for i in range(num_to_replace):
                new_header_content, _, _ = pre_headers[i]
                _, old_header_start_idx, old_header_end_idx = post_headers[i]

                # Add the lines *before* the current old header block
                new_post_lines.extend(post_lines_original[last_copied_post_index + 1 : old_header_start_idx])

                # Add the *new* header block content
                new_post_lines.extend(new_header_content)

                # Update the index to skip the old header block in the original list
                last_copied_post_index = old_header_end_idx

            # Add any remaining lines *after* the last replaced header block
            new_post_lines.extend(post_lines_original[last_copied_post_index + 1 :])

            # 5. Overwrite the post-commit file
            with open(post_commit_path, 'w', encoding='utf-8', errors='ignore') as f_post_write:
                f_post_write.writelines(new_post_lines) # Write lines back

            total_headers_synced += num_to_replace
            synced_files_count += 1
            processed_file = True


        except Exception as e:
            print(f"\nError processing file {filename}: {e}")
            error_files_count += 1
            # Ensure it's not counted as skipped if an error occurred after processing started
            if not processed_file:
                skipped_files_count += 1


    print("\n--- Synchronization Summary ---")
    print(f"Processed files where headers were synced: {synced_files_count}")
    print(f"Total individual header blocks synchronized: {total_headers_synced}")
    print(f"Skipped files (no counterpart, no headers found, etc.): {skipped_files_count}")
    print(f"Files with errors during processing: {error_files_count}")
    print("-----------------------------")

if __name__ == "__main__":
    # --- Ensure directories exist before starting ---
    if not os.path.isdir(PRE_COMMIT_DIR):
        print(f"Error: Source directory '{PRE_COMMIT_DIR}' does not exist.")
        sys.exit(1)
    if not os.path.isdir(POST_COMMIT_DIR):
        print(f"Error: Target directory '{POST_COMMIT_DIR}' does not exist.")
        # Consider creating it if appropriate:
        # os.makedirs(POST_COMMIT_DIR)
        # print(f"Warning: Target directory '{POST_COMMIT_DIR}' did not exist and was created.")
        sys.exit(1) # Exit if target is missing, as it implies user setup error

    synchronize_headers(PRE_COMMIT_DIR, POST_COMMIT_DIR)
    print("Header synchronization process finished.")