import logging
from typing import Any, Dict, List, Tuple
from shasta.ast_node import *
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial
from stream.pipeline_parser import PipelineParser
from stream.mutate import mutate
from stream.run_evaluations import find_scripts
import itertools as it
from pathlib import Path
import os
import subprocess
import hashlib
import re

valid_dirs=[
    "./evaluation_pipelines/valid",
    "./full_benchmark/intercode/pipelines",
    # "./full_benchmark/Shseer",
    "./full_benchmark/pash_benchmark/benchmarks/unix50"
]

output_dir = "./full_benchmark/mutants"
temp_file = os.path.join(output_dir, "temp.sh")

def md5(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()

def pipeline_content_to_id(content: str) -> str:
    sanitized = "".join(c if c.isalnum() else "-" for c in content[:15])
    squashed = re.sub(r'-+', '-', sanitized)
    return squashed + "_" + str(md5(content))

def pipeline_id_to_path(ID, index, output_dir=output_dir) -> Path:
    return Path(os.path.join(output_dir, f"{ID[0]}_P{pipeline_content_to_id(ID[1])}_M{index}.sh"))

def pipeline_to_str(pipeline: PipeNode) -> str:
    return pipeline.pretty()

# todo fixme: why go through the filesystem?
def parse(pipeline_str: str) -> PipeNode | AstNode:
    with open(temp_file, 'w') as f:
        f.write(pipeline_str)
    parser = PipelineParser(temp_file)
    if parser.ast is not None and len(parser.ast) == 1 and len(parser.ast[0]) > 0 and isinstance(parser.ast[0][0], PipeNode):
        return parser.ast[0][0]
    elif parser.ast is not None and len(parser.ast) > 0:
        return parser.ast[0][0]
    else:
        return parser.ast

# PipelineID = (PathStr, ContentStr)

# Dump all mutants of pipelines in `scripts` to `outdir`, and return a mapping from pipeline ID to a list of mutant paths
def dump_mutants(scripts: List['PathStr'], outdir: str) -> Dict['PipelineID', List[str]]:
    mapping = {}
    total = 0
    for script in scripts:
        parser = PipelineParser(script)
        for pipeline in parser.pipeline_nodes:
            ID = (script, pipeline.pretty())
            match pipeline:
                case PipeNode():
                    pass
                case other:
                    logging.warning(f"skipping non-pipeline {ID}, which parsed as {type(other)}: {other}")
                    continue
            logging.info(f"Generating mutants of pipeline {ID}...")
            count = 0
            for i, mutant in enumerate(mutate(pipeline)):
                dump_path = pipeline_id_to_path(ID, i, outdir)
                dump_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dump_path, 'w') as f:
                    f.write(pipeline_to_str(mutant))
                if ID not in mapping:
                    mapping[ID] = []
                mapping[ID].append(dump_path)
                count = i
            logging.info(f"... generated {count + 1} mutants")
            total += count + 1
    logging.info(f"Done! Generated {total} mutants in total")
    return mapping

## filtering plan:
# if we can execute the original pipeline and it doesnt crash
# and the mutated pipeline either crashes or produces different output,
# then we know the mutant has a bug
#
# stricter filter: mutated pipeline doesn't crash (should be much stricter, avoids broken commands)
#
# can we use try? rm's in commands? or just filter them out.

def filter_mutants(mapping: Dict['PipelineID', List[str]]):
    remaining_count = sum(len(mutants) for mutants in mapping.values())

    def remove_mutants(ID, mutants, reason):
        logging.debug(f"Removing all {len(mutants)} mutants of pipeline {ID} because {reason}")
        nonlocal remaining_count
        remaining_count -= len(mutants)
        for mutant in mutants:
            os.remove(mutant)

    for ID, mutants in mapping.items():
        logging.info(f"Filtering mutants of pipeline {ID}...")
        if looks_unsafe(ID[1]):
            remove_mutants(ID, mutants, "it looks unsafe")
            continue

        with open(temp_file, 'w') as f:
            f.write(ID[1])
        crashed, output = run_script(temp_file)
        if crashed:
            remove_mutants(ID, mutants, f"the original pipeline crashed with output `{output}`")
            continue

        for path in mutants:
            crashed, mutant_output = run_script(path)
            if crashed or output == mutant_output:
                logging.debug(f"Removing mutant {path} because it {'crashed' if crashed else 'seems equivalent'} with output `{mutant_output}`")
                os.remove(path)
                remaining_count -= 1
    logging.info(f"Done filtering mutants, leaving {remaining_count} remaining")

def looks_unsafe(pipeline_content: str) -> bool:
    unsafe_commands = ['rm', 'mv', 'cp', 'dd', 'mkfs', 'fdisk', 'shutdown', 'reboot', 'init', 'halt', 'poweroff', 'dd', 'mkfs', 'chmod', 'chown', 'chgrp', 'ln', 'kill', 'killall', 'pkill', 'reboot', 'shutdown', 'init', 'halt', 'poweroff']
    return any(cmd in pipeline_content for cmd in unsafe_commands)

def run_script(path: str) -> Tuple[bool, str]:
    # treat script as crashing if either its exit code is non-zero, it produces output on stderr, or it takes too long
    try:
        result = subprocess.run(["bash", path, "-"], # - in case first arg is a file to cat from
                                input="""
These are
some (80) input
lines
for Testing!
more
  THAN  
5 of them because some benchmarks have a head -n 5
""",
            capture_output=True,
            text=True,
            timeout=2
        )
        crashed = result.returncode != 0 or result.stderr != ""
        output = result.stdout + result.stderr
        return crashed, output
    except subprocess.TimeoutExpired:
        return True, "Script execution timed out"

def main():
    Path(temp_file).parent.mkdir(parents=True, exist_ok=True)
    scripts = find_scripts(valid_dirs)
    mapping = dump_mutants(scripts, output_dir)
    filter_mutants(mapping)

if __name__ == '__main__':
    exit(main())
