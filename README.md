# RT

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
