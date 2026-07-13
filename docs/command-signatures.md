# Command Signatures

Each YAML file in `src/rt/regular_types/database/basic/` defines the input and output types for one command.
The filename (minus `.yaml`) is the command name. Underscores indicate
subcommands: `xargs_cat.yaml` defines the signature for `xargs cat`.

## Fields

| Field | Required | Description |
|---|---|---|
| `input` | yes | Regex the command expects on stdin. `""` means no stdin. |
| `output` | no | Regex or expression for what the command produces on stdout. Defaults to `.*`. |
| `when` | no | List of conditional overrides. Evaluated top-to-bottom, first match wins. |

### `when` entries

| Sub-field | Description |
|---|---|
| `opts` | Short or long options (e.g. `[-n, --print]`) that must be present. Subset check. `flags` is an accepted synonym. |
| `input` | Override `input` for this variant. |
| `output` | Override `output` for this variant. |

## Output Expressions

The `output` field accepts named holes enclosed in `{{ }}`:

| Form | Description | Example |
|---|---|---|
| `{{input}}` | Whatever came in on stdin (pass-through) | `cat`, `sort` |
| `{{$1}}` … `{{$N}}` | The Nth positional argument as a string literal | `echo hello` |
| `{{$@}}` | All positional arguments, space-joined | `echo hello world` |
| `{{<opt>$1}}` … `{{<opt>$N}}` | The Nth argument value of an option flag | `{{d$1}}` for `cut -d,` |
| `{{<opt>$@}}` | All argument values of an option flag, space-joined | `{{d$@}}` |
| `{{@<name>}}` | Resolves `<name>` in the environment; a convention for referring to file contents | `{{@$1}}` |
| `{{@@<name>}}` | Same as `{{@<name>}}`; both strip their prefix and look up `<name>` | `{{@@$1}}` |

For an option like `-d ,`, the option name is the flag with its leading dashes
stripped: `-d` becomes `d`, `--delimiter` becomes `delimiter`. So its argument
values are available as `{{d$1}}`, `{{d$2}}`, and `{{d$@}}`.

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

## Extended Modules

Some commands need computation that can't be expressed in a regex. Write a
Python module in `src/rt/regular_types/database/extended/` instead when:

- The output depends on parsing character sets (`tr`)
- The output depends on interpreting a regex pattern (`grep`, `sed`)
- The output depends on analyzing a script language (`awk`)
- The output depends on complex flag+value interactions (`cut -f`, `tail -n`)

An extended module exports a `resolve` object (an instance of a `TypeResolver`
subclass). Extended modules take priority over any YAML entry with the same
command name.

```
basic/tr.yaml        ← optional YAML fallback (overridden by extended)
extended/tr.py       ← Python resolver (takes priority)
```

## User-Defined Signatures

You can register custom signatures without modifying the repository. Use
`rti --type` to persist a signature for an exact command invocation:

```sh
rti --type '[0-9]+ -> [0-9]+' my_command --my-flag
```

This saves a YAML signature to your platform's user data directory. Rt
automatically loads user-defined signatures alongside the built-in ones, and
user signatures take priority over both basic and extended entries.
