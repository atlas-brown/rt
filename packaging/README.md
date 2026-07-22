# Packaging

Builds `.deb` (Ubuntu), `.rpm` (Fedora), and a Homebrew formula (MacOS) that install `rt` and `rti` system-wide, with no build tools required
on the target machine. Only the checker CLIs are packaged, not the full benchmark reproduction pipeline.

## Installing

### Ubuntu / Fedora

Prebuilt `.deb` and `.rpm` packages are attached to each
[GitHub release](https://github.com/atlas-brown/rt/releases/latest). Each
bundles its own Python runtime and all Python dependencies -- no `uv`,
Python, or Rust toolchain required on the target machine. A JRE is still
required, since the checker loads automaton operations through JPype.

```sh
# Debian / Ubuntu
curl -fsSLO https://github.com/atlas-brown/rt/releases/latest/download/rt-artifact_<version>_amd64.deb
sudo apt install ./rt-artifact_<version>_amd64.deb

# Fedora / RHEL
curl -fsSLO https://github.com/atlas-brown/rt/releases/latest/download/rt-artifact-<version>.x86_64.rpm
sudo dnf install ./rt-artifact-<version>.x86_64.rpm
```

This installs `rt` and `rti` to `/usr/bin`, pulling in a JRE
(`default-jre-headless`/`java-headless`) and `shellcheck` as regular package
dependencies if you don't already have them. Replace `<version>` with the
release version, e.g. `0.1.0`.

