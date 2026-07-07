# Type Definitions

Each YAML file in `basic/` defines the input/output types for one command. The filename (minus `.yaml`) is the command name. Underscores indicate subcommands: `xargs_rm.yaml` defines the type for `xargs rm`.

## Fields

| Field | Required | Description |
|-------|----------|-------------|
| `input` | yes | Regex the command expects on stdin. `""` means no stdin. |
| `output` | yes | Regex or expression for what the command produces on stdout. |
| `when` | no | List of conditional overrides. Evaluated top-to-bottom, first match wins. |

### `when` entries

| Sub-field | Description |
|-----------|-------------|
| `opts` | Options (incl. flags) that must be present (e.g. `[-n, --print]`). Subset check. |
| `input` | Override `input` for this variant. |
| `output` | Override `output` for this variant. |

## Output Expressions

The `output` field accepts these named holes in its expressions:

| Form | Meaning | Example |
|------|---------|---------|
| `{{input}}` | Whatever came in on stdin (pass-through) | `cat`, `sort` |
| `{{$1}}`..`{{$N}}` | Value of Nth positional argument | `echo hello` |
| `{{$@}}` | All positional arguments, space-joined | `echo hello world` |
| `{{d$1}}`..`{{d$N}}` | Value of the Nth positional argument to option -d/--d | `paste -d ',' file1 file2` |
| `{{d$@}}` | All positional arguments to option -d/--d, space-joined
| `{{@<one of the previous forms>}}` | File contents at the path(s) pointed to by the expression | `cat` reads `{{@$1}}` |
| `{{@@<one of the previous forms>}}` | File contents inside the directory/ies pointed to by the expression | `ls {{@@$1}}` |

## Common Patterns

### Pass-through

Command reads stdin and writes it to stdout unchanged.

```yaml
input: .*
output: "{{input}}"
```

### No stdin

Command produces output without reading stdin.

```yaml
input: ""
output: "{{$@}}"
```

### Fixed output

Command always produces the same kind of output.

```yaml
# seq — produces numbers
input: ""
output: "-?[0-9]+"

# yes — produces "y\n"
input: ""
output: "y"
```

### Flag-dependent input

Command accepts different input types depending on opts.

```yaml
# sort — expects numeric input when -n or -h is used
input: .*
output: "{{input}}"
when:
  - opts: [-n, -h]
    input: "[[:blank:]]*[-+]?[0-9]+.*"
```

### Flag-dependent output

Command produces different output when a flag is present.

```yaml
input: .*
output: "{{input}}"
when:
  - opts: [-q]
    output: ""
```

### File content output

Command reads a file and produces its contents.

```yaml
# cat — outputs file contents, doesn't use stdin
input: ""
output: "{{@$1}}"
```

## When to Use an Extended Module

Some commands need computation that can't be expressed in regex. Write a Python module in `extended/` instead when:

- The output depends on parsing character sets (`tr`)
- The output depends on interpreting a regex pattern (`grep`, `sed`)
- The output depends on analyzing a script language (`awk`)
- The output depends on complex flag+value interactions (`cut -f`, `tail -n`)

An extended module exports a `resolve` callable and lives alongside the YAML file:

```
basic/tr.yaml        ← YAML (can exist, will be overridden)
extended/tr.py       ← Python resolver
```
