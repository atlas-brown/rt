#!/usr/bin/env bash
# Do not use this script manually, Use makefile

set -e

go clean ./...
gotestsum -- $(go list ./... | grep -v mocks)
