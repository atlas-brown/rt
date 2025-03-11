#!/usr/bin/env python
import os
import logging
import csv
import re
from typing import List, Optional, Tuple
from stream.shell_parser_util import extract_pipe_nodes_from_file, get_command_invocation, parse_shell_to_asts
from shasta.ast_node import CommandNode
from pash_annotations.datatypes.CommandInvocationInitial import CommandInvocationInitial

class ShellParser:
    def __init__(self, pipeline_address: str, extract_all_pipelines: bool = True) -> None:
        self.pipeline_address = pipeline_address
        self.extract_all_pipelines = extract_all_pipelines
        self.pipeline_nodes = extract_pipe_nodes_from_file(self.pipeline_address, self.extract_all_pipelines)

    def process_command_invocation(self, command_invocation: CommandInvocationInitial, command_node: CommandNode, pipeline_str: str) -> Optional[Tuple[str, str, str, str, str]]:
        command_name = command_invocation.cmd_name.lower()
        if command_name not in {"tr", "cut", "sed", "rev"}:
            return None
        flags = sorted([flag.get_name() for flag in command_invocation.flag_option_list])
        flags_str = " ".join(flags)
        full_command = command_node.pretty()
        if command_name == "sed":
            sed_regex = r'\bs(?P<delim>.)(?P<pattern>(?:\\.|(?!\1).)+)(?P=delim)'
            m = re.search(sed_regex, full_command)
            if m:
                pattern_found = m.group("pattern")
                if pattern_found in {"$", "^"}:
                    return None
            if re.search(r'\b\d*d\b', full_command) or re.search(r'"\d*d"', full_command):
                category = "full stream transformation"
            else:
                category = "line-based transformation"
            return (category, command_name, flags_str, full_command, pipeline_str)
        if command_name == "tr":
            if "\\n" in full_command:
                category = "full stream transformation"
            else:
                category = "line-based transformation"
            return (category, command_name, flags_str, full_command, pipeline_str)
        if command_name == "cut":
            category = "line-based transformation"
            return (category, command_name, flags_str, full_command, pipeline_str)
        if command_name == "rev":
            category = "line-based transformation"
            return (category, command_name, flags_str, full_command, pipeline_str)
        return None

    def parse_pipeline(self) -> List[Tuple[object, List[Tuple[CommandInvocationInitial, CommandNode]]]]:
        if self.pipeline_nodes is None:
            raise ValueError("Parsing failed")
        pipelines = []
        for node in self.pipeline_nodes:
            commands_in_pipe: List[Tuple[CommandInvocationInitial, CommandNode]] = []
            for cmd_node in node.items:
                cmd_invocation = get_command_invocation(cmd_node)
                commands_in_pipe.append((cmd_invocation, cmd_node))
            pipelines.append((node, commands_in_pipe))
        return pipelines

def find_sh_files(paths: List[str]) -> List[str]:
    sh_files = []
    for path in paths:
        if os.path.isfile(path) and path.endswith(".sh"):
            sh_files.append(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".sh"):
                        sh_files.append(os.path.join(root, file))
    return sh_files

def main():
    logging.basicConfig(level=logging.INFO)
    directories = [
        ("./evaluation_pipelines/valid", True),
        ("./full_benchmark/intercode/pipelines", True),
        ("./full_benchmark/pash_benchmark/benchmarks/unix50", True),
        ("./evaluation_pipelines/invalid", True),
        ("./full_benchmark/curated_mutants", True),
        ("./full_benchmark/llm_injection/pipelines", True),
    ]
    results = []
    for directory, extract_all in directories:
        sh_files = find_sh_files([directory])
        for sh_file in sh_files:
            logging.info(f"Processing file: {sh_file}")
            try:
                sp = ShellParser(sh_file, extract_all_pipelines=extract_all)
                pipelines = sp.parse_pipeline()
                for pipeline_node, commands in pipelines:
                    pipeline_str = pipeline_node.pretty()
                    for command_invocation, command_node in commands:
                        row = sp.process_command_invocation(command_invocation, command_node, pipeline_str)
                        if row is not None:
                            results.append(row)
            except Exception as e:
                logging.error(f"Error processing file {sh_file}: {e}")
    category_order = {"line-based transformation": 0, "full stream transformation": 1}
    results.sort(key=lambda x: (category_order.get(x[0], 99), x[1], x[2]))
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_csv = os.path.join(script_dir, "output.csv")
    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["category", "command", "flags", "full_command", "pipeline"])
        for row in results:
            writer.writerow(row)

if __name__ == "__main__":
    main()
