#!/bin/bash

set -ex

GH_ARCH="amd64"

################################################################################
# Commit message: fix: remove retry-all-errors option [skip ci]
# Commit URL: https://github.com/VSCodium/vscodium/commit/fc770788681fab2079ee60fe3ad13c979a5dd22d
# Category: 
# Notes: 
# Changed content:
# - VERSION=`curl --retry 12 --retry-delay 30 --retry-all-errors "https://api.github.com/repos/cli/cli/releases/latest" | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/' | cut -c2-`
# + VERSION=`curl --retry 12 --retry-delay 30 "https://api.github.com/repos/cli/cli/releases/latest" | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/' | cut -c2-`
################################################################################
# put stream annotation here
# stream enable
VERSION=`curl --retry 12 --retry-delay 30 --retry-all-errors "https://api.github.com/repos/cli/cli/releases/latest" | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/' | cut -c2-`

curl --retry 12 --retry-delay 120 --retry-all-errors -sSL "https://github.com/cli/cli/releases/download/v${VERSION}/gh_${VERSION}_linux_${GH_ARCH}.tar.gz" -o "gh_${VERSION}_linux_${GH_ARCH}.tar.gz"

tar xf "gh_${VERSION}_linux_${GH_ARCH}.tar.gz"

cp "gh_${VERSION}_linux_${GH_ARCH}/bin/gh" /usr/local/bin/

gh --version