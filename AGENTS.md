# Guidelines

* An overview of the system can be found in `docs/architecture.md`
* Run the system using `uv run rt`
* Run the tests using `uv run pytest`
* If `libdash` installation is failing:
  * Export `CFLAGS=-std=gnu17`
  * Use git+https://github.com/binpash/libdash instead of PyPI
