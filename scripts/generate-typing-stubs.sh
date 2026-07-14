#! /usr/bin/env sh

err_msg=$(uv run python - <<'EOF' 2>&1 >/dev/null
# This file is used to automatically generate typing stubs for the Java classes used in the project
import stubgenj

from rt.java_api import ensure_jvm

ensure_jvm()

# Import all packages for which typing stubs are needed
import dk.brics

stubgenj.generateJavaStubs([dk.brics], useStubsSuffix=False, outputDir="typings", jpypeJPackageStubs=False)
EOF
)

# shellcheck disable=SC2181
if [ $? -ne 0 ]; then
    echo "Failed:"
    echo "${err_msg}"
    exit 1
fi

echo "Done"
