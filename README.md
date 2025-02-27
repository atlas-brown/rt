# StreamTypes

## Install dependencies (Ignore if building from Docker)

```bash
pip3 install shasta libdash pash_annotations pytest z3-solver
```

## Run evaluations

```bash
./run_evaluations.sh # with annotations; logging level: INFO; 1 worker; no timeout
./run_evaluations.sh --log_level DEBUG # logging level: DEBUG
./run_evaluations.sh --disable_annotation # without annotations
# currently not supported
./run_evaluations.sh --workers 16 # 16 workers
./run_evaluations.sh --timeout 30 # timeout for each z3 query: 30 seconds
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
cat $1 | cut -f 2 | sort -n | uniq -c | sort -nr | head -n 1 | tr -s ' ' '\n' | tail -n 1
```

* @assume: The output type of the command is assumed to be the given regular language.
* @assert: Type checker will check if the output type of the command is the subset of the given regular language.
* @expect: The expected input type of the command is given.
* @input: The input type of the pipeline (default: "")
* @output: The output type of the pipeline