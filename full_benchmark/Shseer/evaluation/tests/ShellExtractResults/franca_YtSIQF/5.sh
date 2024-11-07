#!/bin/sh
# (C) Gunnar Andersson
# This file is part of franca_install_automation
# License: http://creativecommons.org/licenses/by/4.0/

# Test that URLs are still valid
# This is a quick smoke test, suitable to be run often
# and to warn and to warn if URLs go stale

failed=""
missing=""
p="$PWD"
cd "$(dirname $0)"

test_url() {
   # Fetching head is not really that robust way to find out
   # but let's test for 404 not found and 403 forbidden to start with
   f=""
   curl --head --silent "$2" | egrep -q "404|403" && f=true
   if [ "$f" = "true" ] ; then
      failed=true
      missing="$1 at $2\n$missing"
   fi
}

# Nullify a function used by CONFIG script
if_vagrant() {
   :
}

# Source config, then test each URL
. ../CONFIG
test_url ECLIPSE_INSTALLER_i686 "$ECLIPSE_INSTALLER_i686"
test_url ECLIPSE_INSTALLER_x86_64 "$ECLIPSE_INSTALLER_x86_64"
test_url DBUS_EMF_UPDATE_SITE_URL "$DBUS_EMF_UPDATE_SITE_URL"
test_url GEF4_UPDATE_SITE_URL "$GEF4_UPDATE_SITE_URL"
test_url FRANCA_ARCHIVE_URL "$FRANCA_ARCHIVE_URL"
test_url EXAMPLES_URL "$EXAMPLES_URL"

cd "$p"

if [ -n "$failed" ] ; then
   echo Missing URLs:
   cat<<EOT
$missing
EOT
   exit 1
else
   echo OK
   exit 0
fi

