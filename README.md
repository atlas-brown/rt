# StreamTypes

## Installation

### Native (Linux)

Make sure you have the following installed:
* `git`
* `make`
* `automake`
* `autoconf`
* `libtool`
* [`uv`](https://github.com/astral-sh/uv) (recommended) or `pipx`

Then, run:
```bash
uv tool install git+https://github.com/brown-cs2952r/StreamTypes.git
uv tool update-shell  # If PATH needs to be updated
```

Or:

```bash
pipx install git+https://github.com/brown-cs2952r/StreamTypes.git
pipx ensurepath  # If PATH needs to be updated
```

### Containerized (Linux, MacOS)

Unfortunately some of the dependencies don't build on MacOS, so the best option for now is using a Docker image.

To install:

```bash
git clone https://github.com/brown-cs2952r/StreamTypes.git
docker build --target sys -t rt ./StreamTypes
docker run --rm rt --help  # Should output a help message
rm -rf ./StreamTypes
```

**(IMPORTANT)** To run:

```bash
# RT needs to be able to either accept interactive input, or read files on the host machine, so it must be run as:
docker run --rm -i -v "$(pwd)":/ws -w /ws rt file.sh
# Thus, it's recommended to create an alias or a function:
echo "alias rt='docker run --rm -i -v \"\$(pwd)\":/ws -w /ws rt'" >> ~/.bashrc  # Or equivalent rc file
```

Use `rt file.sh` to check a script. Use `rtr check file.sh` for the same script-checking path, or `rtr resolve COMMAND ...` to inspect one command invocation's regular type.


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
