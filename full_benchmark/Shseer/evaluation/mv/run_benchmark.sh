#!/bin/bash

# Guard number of flags
if [ $# -le 0 ]; then
    echo $#
    echo "Flags => [--use_existing]"
    echo "Collect evaluation"
    echo ""
    echo "options:"
    echo "-h, --help            show this help message and exit"
    echo "--github              Run Shseer against the github scripts"
    echo "--llm                 Run Shseer against the llm-generated scripts"
    echo "--debian              Run Shseer against the debian scripts"
    echo "--all                 Run Shseer against all scripts"
    echo "--no_perf             Run Shseer in parallel and ignore performance tests"
    echo "--commit_id COMMIT_ID"
    echo "    Override commit id"
    exit
fi

if [[ $* == *--use_existing* ]]; then
    echo "Using existing"
    cd Shseer
    commit_id=`git rev-parse HEAD`
    cd ..
else
    echo "Re-cloning"
    # Manual merge evaluation folder with main branch
    rm -rf Shseer
    git clone -b testing_scripts --single-branch git@github.com:binpash/Shseer.git || (echo "Cannot clone"; exit)
    mv Shseer/evaluation . || (echo "Cannot move"; exit)
    rm -rf Shseer
    git clone -b master --single-branch git@github.com:binpash/Shseer.git || (echo "Cannot clone"; exit)
    cd Shseer
    commit_id=`git rev-parse HEAD`
    cd ..
    mv evaluation Shseer || (echo "Cannot move"; exit)
fi

# Run the evaluation with the flags
cd Shseer/evaluation
echo python3 collect_point.py "$@" --commit_id $commit_id --filepath ../../versions_overtime.json
python3 collect_point.py "$@" --commit_id $commit_id --filepath ../../versions_overtime.json