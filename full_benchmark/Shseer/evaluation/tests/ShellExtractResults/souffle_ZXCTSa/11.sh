#!/bin/bash

set -e
set -x

envsubst '${RELEASE_TAG},${REPO_OWNER}' < PKGBUILD.in  > PKGBUILD
makepkg
makepkg --printsrcinfo > .SRCINFO
