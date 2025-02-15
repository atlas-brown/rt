# StreamTypes

## Install dependencies

```bash
pip3 install shasta libdash pash_annotations pytest z3-solver
```

## Run evaluations

```bash
./run_evaluations.sh # with annotations; logging level: INFO; 1 worker
./run_evaluations.sh --log_level DEBUG # with annotations; logging level: DEBUG; 1 worker
./run_evaluations.sh --user_annotations false # without annotations; logging level: INFO; 1 worker
./run_evaluations.sh --num_workers 16 # with annotations; logging level: INFO; 16 workers
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