#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

message=""
message_specified=0
force_push=0
mode="commit"
snapshot_dir=""
commit_created=0

usage() {
  cat <<'EOF'
Usage: bash scripts/push_snapshot.sh [options]

Create a snapshot from the local committed tree and push it to github/main
using the local repository git user.name and user.email.

Options:
  -m, --message <msg>  Snapshot commit message inside the temporary repo.
                       Default: snapshot for commit mode, init for
                       --clean-history, keep existing message for --amend.
      --commit         Create a normal commit on top of github/main.
                       This is the default mode.
      --clean-history  Create a fresh snapshot repo with a root commit.
      --amend          Reuse an existing snapshot repo and amend its last
                       commit. Requires --snapshot-dir.
      --snapshot-dir <dir>
                       Snapshot directory to create or reuse. If omitted,
                       a new temporary directory is made.
      --force          Force-push to github/main.
  -h, --help           Show this help message.

Notes:
  - This does not create a commit in the local repository.
  - By default this snapshots local HEAD only.
  - Uncommitted and untracked files are not included.
  - The snapshot directory is kept and printed at the end.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--message)
      if [[ $# -lt 2 ]]; then
        echo "error: missing value for $1" >&2
        exit 1
      fi
      message="$2"
      message_specified=1
      shift 2
      ;;
    --commit)
      mode="commit"
      shift
      ;;
    --clean-history)
      mode="clean-history"
      shift
      ;;
    --amend)
      mode="amend"
      shift
      ;;
    --snapshot-dir)
      if [[ $# -lt 2 ]]; then
        echo "error: missing value for $1" >&2
        exit 1
      fi
      snapshot_dir="$2"
      shift 2
      ;;
    --force)
      force_push=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

remote_url="$(git remote get-url github)"
user_name="$(git config user.name || true)"
user_email="$(git config user.email || true)"

sync_committed_tree() {
  find "$snapshot_dir" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
  git archive --format=tar HEAD | tar -xf - -C "$snapshot_dir"
}

configure_snapshot_repo() {
  if [[ -n "$user_name" ]]; then
    git -C "$snapshot_dir" config user.name "$user_name"
  fi
  if [[ -n "$user_email" ]]; then
    git -C "$snapshot_dir" config user.email "$user_email"
  fi
}

ensure_snapshot_remote() {
  if git -C "$snapshot_dir" remote get-url github >/dev/null 2>&1; then
    git -C "$snapshot_dir" remote set-url github "$remote_url"
  else
    git -C "$snapshot_dir" remote add github "$remote_url"
  fi
}

checkout_snapshot_main() {
  if git -C "$snapshot_dir" show-ref --verify --quiet refs/remotes/github/main; then
    git -C "$snapshot_dir" checkout -B main github/main >/dev/null 2>&1
  elif git -C "$snapshot_dir" show-ref --verify --quiet refs/remotes/origin/main; then
    git -C "$snapshot_dir" checkout -B main origin/main >/dev/null 2>&1
  elif git -C "$snapshot_dir" rev-parse --verify main >/dev/null 2>&1; then
    git -C "$snapshot_dir" checkout main >/dev/null 2>&1
  else
    git -C "$snapshot_dir" checkout -b main >/dev/null 2>&1
  fi
}

if [[ "$mode" == "commit" ]]; then
  if [[ -z "$snapshot_dir" ]]; then
    snapshot_dir="$(mktemp -d "${TMPDIR:-/tmp}/streamtypes-worktree-snapshot.XXXXXX")"
    if ! git clone --branch main --single-branch "$remote_url" "$snapshot_dir" >/dev/null 2>&1; then
      rm -rf "$snapshot_dir"
      snapshot_dir="$(mktemp -d "${TMPDIR:-/tmp}/streamtypes-worktree-snapshot.XXXXXX")"
      git -C "$snapshot_dir" init -b main >/dev/null
    fi
  else
    snapshot_dir="$(mkdir -p "$snapshot_dir" && cd "$snapshot_dir" && pwd)"
    if [[ -d "$snapshot_dir/.git" ]]; then
      :
    elif [[ -z "$(find "$snapshot_dir" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
      if ! git clone --branch main --single-branch "$remote_url" "$snapshot_dir" >/dev/null 2>&1; then
        git -C "$snapshot_dir" init -b main >/dev/null
      fi
    else
      echo "error: snapshot dir is not a git repository: $snapshot_dir" >&2
      exit 1
    fi
  fi

  configure_snapshot_repo
  ensure_snapshot_remote
  git -C "$snapshot_dir" fetch github main >/dev/null 2>&1 || true
  checkout_snapshot_main
  sync_committed_tree
  git -C "$snapshot_dir" add -A

  if git -C "$snapshot_dir" diff --cached --quiet; then
    echo "No changes to commit."
  else
    if [[ "$message_specified" -eq 0 ]]; then
      message="snapshot"
    fi
    git -C "$snapshot_dir" commit -m "$message" >/dev/null
    commit_created=1
  fi
elif [[ "$mode" == "clean-history" ]]; then
  if [[ -z "$snapshot_dir" ]]; then
    snapshot_dir="$(mktemp -d "${TMPDIR:-/tmp}/streamtypes-worktree-snapshot.XXXXXX")"
  else
    snapshot_dir="$(mkdir -p "$snapshot_dir" && cd "$snapshot_dir" && pwd)"
    if [[ -n "$(find "$snapshot_dir" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
      echo "error: snapshot dir is not empty: $snapshot_dir" >&2
      exit 1
    fi
  fi

  sync_committed_tree
  git -C "$snapshot_dir" init -b main >/dev/null
  configure_snapshot_repo
  ensure_snapshot_remote
  git -C "$snapshot_dir" add -A

  if [[ "$message_specified" -eq 0 ]]; then
    message="init"
  fi

  git -C "$snapshot_dir" commit -m "$message" >/dev/null
  commit_created=1
elif [[ "$mode" == "amend" ]]; then
  if [[ -z "$snapshot_dir" ]]; then
    echo "error: --amend requires --snapshot-dir" >&2
    exit 1
  fi

  snapshot_dir="$(cd "$snapshot_dir" && pwd)"

  if [[ ! -d "$snapshot_dir/.git" ]]; then
    echo "error: snapshot dir is not a git repository: $snapshot_dir" >&2
    exit 1
  fi

  configure_snapshot_repo
  ensure_snapshot_remote
  checkout_snapshot_main
  sync_committed_tree
  git -C "$snapshot_dir" add -A
  if [[ "$message_specified" -eq 1 ]]; then
    git -C "$snapshot_dir" commit --amend -m "$message" >/dev/null
  else
    git -C "$snapshot_dir" commit --amend --no-edit >/dev/null
  fi
  commit_created=1
else
  echo "error: unsupported mode: $mode" >&2
  exit 1
fi

if [[ "$force_push" -eq 1 ]]; then
  git -C "$snapshot_dir" push --force github HEAD:main
else
  git -C "$snapshot_dir" push github HEAD:main
fi

last_message="$(git -C "$snapshot_dir" log -1 --pretty=%s 2>/dev/null || true)"

echo "Snapshot push complete."
echo "snapshot_dir=$snapshot_dir"
echo "remote=github"
echo "branch=main"
echo "mode=$mode"
echo "force_push=$force_push"
echo "commit_created=$commit_created"
echo "message=${last_message:-<none>}"
