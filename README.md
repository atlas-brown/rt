# StreamTypes

## Install dependencies (Ignore if building from Docker)

```bash
pip3 install shasta libdash pash_annotations pytest jpype1
```


## Test things out

Use `typecheck.sh`; see `-h` for details
``` bash
sh typecheck.sh -h
```




## Run evaluations

```bash
./run_evaluations.sh # with annotations; logging level: INFO; 1 worker; no timeout
./run_evaluations.sh --log_level DEBUG # logging level: DEBUG
./run_evaluations.sh --disable_annotation # without annotations
# currently not supported
# ./run_evaluations.sh --workers 16 # 16 workers
# ./run_evaluations.sh --timeout 30 # timeout for each z3 query: 30 seconds
```

## Run unit tests

```bash
sh run_tests.sh
```

## Debug

```bash
PYTHONPATH=src python3 src/stream/debug.py
```

## User Annotations (Provisional)

```bash
# @assume "cat $1" --> ".* .*"
# @assume "cut -f 2" --> "[0-9]+"
# @assert "head -n 1" --> ".* .*"
# @expect "[0-9]+" --> "sort -n"
# @input ""
# @output "[^ ]+"
# @file "$1" "[0-9]+\t[0-9]+"
cat $1 | cut -f 2 | sort -n | uniq -c | sort -nr | head -n 1 | tr -s ' ' '\n' | tail -n 1
```

* @assume: The output type of the command is assumed to be the given regular language.
* @assert: Type checker will check if the output type of the command is the subset of the given regular language.
* @expect: The expected input type of the command is given.
* @input: The input type of the pipeline (default: "")
* @output: The output type of the pipeline
* @file: The type of the file content. The first argument is the file name, and the second argument is the regular language.

## Github Commits Benchmark Annotations

* Search for `# stream enable` in the `full_benchmark/github_repos_commits/output_new` directory to locate relevant commits. 
* If any change falls outside the scope, remove the line `# stream enable` above the change. 
* If the change is within the scope, replace the line `# put stream annotation here` with the user annotations if necessary.
