#!/usr/bin/env bash
# Do not use this script manually, Use makefile

set -e

# gotestsum, used by `make test`. Test utilities
echo "Installing gotestsum"
go install gotest.tools/gotestsum@v1.12.0

# rice, used by `make build`. Embed UI dist into go binary
echo "Installing rice"
go install github.com/GeertJohan/go.rice/rice@v1.0.3

# mockery, used by `make mocks`. Generating mock for backend
echo "Installing mockery"
go install github.com/vektra/mockery/v2@v2.46.2

# revproxy, usef by `make proxy`. Start a proxy for test
echo "Installing revproxy"
go install github.com/jsdidierlaurent/revproxy@latest
