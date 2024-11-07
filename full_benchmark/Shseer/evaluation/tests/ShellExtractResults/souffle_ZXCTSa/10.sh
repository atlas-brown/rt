#!/bin/bash

set -oue pipefail

if [ ! $(which clang-format) ]
then
    echo "Error: program 'clang-format' not found!"
    exit 1
fi

if [ "$(clang-format --version | sed 's/.*version //;s/\..*//')" -lt "7" ]
then
   echo "Error: program 'clang-format' must be version 7 or later!"
   exit 1
fi

# Some of the git tools can set this variable, which can cause problems
# https://magit.vc/manual/magit/My-Git-hooks-work-on-the-command_002dline-but-not-inside-Magit.html
unset GIT_LITERAL_PATHSPECS

#Change the delimiter used by 'for' so we can handle spaces in names
IFS=$'\n'
for FILE in $(git diff --diff-filter=d --cached --name-only "*.cpp" "*.h")
do
    # Store the current version in case it has been modified
    TMPFILE="$(mktemp)"
    cp "$FILE" "$TMPFILE"
    # Temporarily remove modified versions, if they exist
    git checkout -q "$FILE"
    # Format
    clang-format -i -style=file "$FILE"
    # Add the formatted file
    git add "$FILE"
    # Restore the old, possibly modified version
    mv "$TMPFILE" "$FILE"
    # Format the uncached version to keep it in sync with the cached
    clang-format -i -style=file "$FILE"
done

# Don't commit if there are no changes to commit
test "$(git diff --cached)" != ""
