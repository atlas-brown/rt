# Running Evaluation

Make sure to install the requirements for Shseer before running

Use the shell script run_benchmark.sh to merge the benchmark and master branch together to add a data point of number of good scripts, bad scripts, Shseer panics, Shseer crashes, and timeouts.

## Command Line Flags

--use_existing, Will avoid cloning and use existing code
--github, Add GitHub scripts to the evaluation
--debian, Add debian scripts to the evaluation
--llm, Add llm generated scripts to the evaluation
--all, Run all groups (github, debian, llm) in evaluation
--no_perf, Run Shseer in parallel. Recommended for large evaluations like the debian scripts. Ignore performance results if this flag is used.
--filepath, The output file
