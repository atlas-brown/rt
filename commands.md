# Commands

For a given command, we need  all combination of the listed flags.

All commands should support varadic arguments ideally and if not at least 5 args in place of the varadic arg. Example: rm takes any number of files, so we should have specs for rm taking at least 5 files.

A major catch here is modelling the behavior correctly. For example:

``` rm foo boo goo ```

will delete `boo`and `goo` even if foo does not exist before exiting with non-zero exit code. This needs to be modelled correctly

| Command | Flag | Status |
| --- | ---- | --- |
| rm | -r,-f,-d,-R | | 
| mv
| cp | -R
| cat | all flags 
| mkdir | all flags
