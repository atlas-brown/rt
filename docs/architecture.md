# Architecture

## Overview

Rt statically checks shell pipelines. It parses a shell script, walks each
pipeline command-by-command, and verifies that the data one command produces is
compatible with what the next command expects. Incompatibilities are reported
with concrete counterexamples.

The core analytical capability comes from using **finite automata** as the type
system: instead of coarse categories like "text" or "numbers", the checker
reasons about the precise shape of data (e.g. "lines of the form
`[0-9]+,[0-9]+`").

## Core Components

### 1. Entry Point

The **entry point** reads shell scripts (or interactive stdin input), drives
the checking pipeline, and reports results. Exposed as the `rt` CLI. A
companion tool, `rti`, provides interactive command-type inspection and
annotation registration.

### 2. Script Parser

The **script parser** parses shell scripts into abstract syntax trees,
extracting pipelines (sequences of commands connected by pipes) and
user-supplied annotations embedded in comments.

### 3. Type Database

The **type database** is the registry of known command behaviors. Each entry
specifies:
- A command's default input and output type
- How arguments and flags modify its behavior
- Rules that map specific flag/argument combinations to concrete type
  transformations

Complex commands (e.g. `sed`, `awk`, `grep`) have programmatic profiles that
dynamically build transformation logic; simpler commands use declarative
configuration.

### 4. Orchestrator

The **orchestrator** iterates over every pipeline in the script, delegating
each to a pipeline analyzer. Acts as the top-level driver.

### 5. Pipeline Analyzer

The **pipeline analyzer** checks a single pipeline. Walks the commands
left-to-right:

1. Retrieves a **command signature** from the type database
2. Derives a **command type** for this specific invocation (considering flags,
   arguments, and user annotations)
3. Applies the command type to the current **stream type** (the output of the
   previous command)
4. Produces a new stream type (this command's output)
5. Checks three kinds of violations:
   - **Input mismatch** — the incoming data does not fit what the command expects
   - **Empty output** — the command always produces nothing (a likely bug)
   - **Annotation failure** — a user annotation (`@assert`, `@output`) is
     violated
6. Passes the new stream type to the next command

Each violation carries a counterexample — a concrete string that triggers the
mismatch.

### 6. Stream Type

A **stream type** is the central abstraction representing the data flowing
through a pipe at a given point. Backed by a deterministic finite automaton
(DFA). Stream types describe individual lines of data.

**Operations**: subset check, intersection, union, difference, complement,
concatenation, Kleene star/plus, optional, reversal.

### 7. Command Type

A **command type** represents a command's input-output relationship. Two
varieties:

- **Fixed output**: the output is always the same regardless of input
  (e.g. `echo hello` always outputs `hello`).
- **Input-dependent**: the output is computed from the input using a
  **transformation** (e.g. `grep [0-9]` filters input lines containing
  digits).

An input-dependent command type is conceptually a polymorphic function: *for any
input type `α`, the output is `f(α)`*, where `f` is a transformation that may
reference `α`.

### 8. Transformation

A **transformation** is a composable tree of AST nodes representing data
transformations. Each node, given an environment mapping names to stream types,
evaluates to a stream type. Input-dependent command types bind the input to the
name `α` in the environment before evaluation.

**Leaf nodes**: constants, input references, regex patterns.
**Internal nodes**: regular language operations (union, intersection,
concatenation, complement, Kleene star, optional, reversal) and
command-specific operations (character translation, character deletion, field
selection, match-and-replace, line extraction, first/last N lines).

### 9. Stream Transformer

A **stream transformer** is a finite-state transducer (FST) — an automaton
paired with an output function. Models character-level transformations: for
each character consumed, zero or more characters are emitted. Used when a
command's effect cannot be expressed purely at the regular-language level
(e.g. `tr` maps individual characters, `cut` selects delimited fields, `head`
keeps only the first N lines).

Applying a stream transformer to a stream type computes the language of all
possible outputs given the language of all possible inputs — a standard
automaton product construction.

### 10. Regex Parser

The **regex parser** parses regular expressions into two parallel
representations:
- An AST (for structural manipulation: anchoring, hole-filling)
- A DFA (for computational operations: subset check, intersection)

Supports character classes, ranges, complements, intersections, POSIX classes,
and template holes (for polymorphic types).

### 11. User Annotations

**User annotations** are inline directives in shell script comments that can be
attached to pipelines or individual commands. Parsed from `# @` comments:

| Directive | Syntax | Meaning |
|---|---|---|
| **Assume** | `# @assume "invocation" --> "regex"` | Treat this command as producing exactly this type |
| **Expect** | `# @expect "regex" --> "invocation"` | This command requires exactly this input type |
| **Assert** | `# @assert "invocation" --> "regex"` | Verify that this command's output conforms to this type |
| **Assert Contains** | `# @assert_contains "invocation" --> "regex"` | Verify that the command's input contains strings matching this type |
| **Input** | `# @input "regex"` | Declare the pipeline's expected input type |
| **Output** | `# @output "regex"` | Assert the pipeline's output conforms to this type |
| **Output Contains** | `# @output_contains "regex"` | Verify that the pipeline's output contains strings matching this type |
| **File / Var** | `# @file "$v" : "regex"` / `# @var "$v" : "regex"` | Declare the type of a file operand or shell variable |
| **Concretize** | `# @concretize "varname" --> "path"` | Snapshot a file's contents into a type at check time |

### 12. Automaton Engine

The **automaton engine** is an external library providing core DFA operations:
determinization, minimization, subset test, intersection, union, difference,
emptiness test, shortest-example extraction. Accessed through a thin
language-binding layer so the rest of the system is decoupled from the specific
engine.

## Data Flow

```
Shell Script
    │
    ▼
script parser ──► pipeline ASTs + user annotations
    │
    ▼
orchestrator ──► for each pipeline:
    │
    ▼
pipeline analyzer
    │
    │   for each command (left to right):
    │
    ├── Look up command signature in type database
    ├── Derive command type (flags, args, user annotations)
    ├── Apply command type to current stream type
    │     │
    │     └── Input-dependent types evaluate a transformation,
    │          which may use stream transformers for character-level transforms
    │
    ├── Produces new stream type (command's output)
    ├── Check input compatibility (subset check via automaton engine)
    ├── Check heuristic rules (e.g., empty output)
    ├── Check user annotations
    └── Advance to next command
    │
    ▼
violation reports (with counterexamples)
```

## Component Diagram

```
┌─────────────┐     ┌────────────────┐     ┌───────────────────┐
│ entry point │────►│  orchestrator  │────►│  script parser    │
└─────────────┘     └───────┬────────┘     └─────────┬─────────┘
                            │                        │
                            │              ┌─────────▼──────────┐
                            │              │   type database    │
                            │              └─────────┬──────────┘
                            │                        │
                    ┌───────▼────────┐     ┌─────────▼──────────┐
                    │ pipeline       │◄────│ command signature    │
                    │ analyzer       │     └────────────────────┘
                    └───────┬────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
    ┌─────────▼──────┐ ┌────▼───────┐ ┌───▼─────────────┐
    │ stream type    │ │ command    │ │ user annotations│
    │  (automaton)   │ │ type       │ │                 │
    └────────┬───────┘ └───┬────────┘ └─────────────────┘
             │             │
    ┌────────▼──────┐ ┌────▼───────────┐
    │ automaton     │ │ transformation │
    │ engine        │ │                │
    └───────────────┘ └───┬────────────┘
                          │
                  ┌───────▼────────┐
                  │ stream         │
                  │ transformer    │
                  │ (FST)          │
                  └────────────────┘
```

## Key Design Principles

1. **Regular types, not coarse types.** Data is modeled as regular languages
   (finite automata) rather than traditional type categories. This provides
   precision: the checker can detect that `cut -f2 -d:` output is incompatible
   with a command expecting `[0-9]+` lines.

2. **Polymorphism through transformations.** Most commands are modeled as
   input-dependent: *for input `α`, the output is computed by evaluating a
   transformation parameterized by `α`*. This captures real command
   semantics (`grep` filters, `cut` selects fields) without requiring a fixed
   output type per command.

3. **Declarative configuration, programmatic escape hatch.** Simple commands
   use YAML configuration files; complex commands use programmatic profiles
   that build transformations dynamically.

4. **User annotations for precision.** Inline `# @` comment directives let
   users refine inferred types, express expectations, and verify properties —
   making the checker useful even when static inference alone would be
   imprecise.

5. **Concrete counterexamples.** Every type error includes a witness string,
   showing the user exactly what data causes the incompatibility.

## Module Map

| Concept | Module |
|---|---|
| Entry point (`rt` CLI) | `src/rt/main.py` |
| Entry point (`rti` CLI) | `src/rti/main.py` |
| Script parser | `src/rt/shell/parser.py` |
| Type database (registry) | `src/rt/regular_types/database/registry.py` |
| Type database (resolver) | `src/rt/regular_types/database/resolver.py` |
| Declarative command signatures | `src/rt/regular_types/database/basic/` |
| Programmatic command signatures | `src/rt/regular_types/database/extended/` |
| Orchestrator + pipeline analyzer | `src/rt/type_checking/checker.py` |
| Stream type | `src/rt/regular_types/stream_type.py` |
| Command type | `src/rt/regular_types/command_type.py` |
| Transformation | `src/rt/regular_types/stream_transform.py` |
| Stream transformer (FST) | `src/rt/transducer.py` |
| Regex parser + AST | `src/rt/regex/parser.py`, `src/rt/regex/ast.py` |
| User annotations | `src/rt/type_checking/annotations.py` |
| Heuristic checks | `src/rt/type_checking/heuristics.py` |
| Automaton engine (Java bridge) | `src/rt/java_api.py` |
| Error formatting | `src/rt/format.py` |
