#!/bin/sh
# (C) 2015 Gunnar Andersson
# This file is part of franca_install_automation
# License: See project directory

if [ -z "$PREFERRED_JAVA_VERSION" ] ; then
  echo "Variable PREFERRED_JAVA_VERSION is not defined"
else
   java -version >/dev/null 2>&1 || warn "Could not run java executable to check version!?"
   java -version 2>&1 | fgrep -q $PREFERRED_JAVA_VERSION || warn "Your java version is not $PREFERRED_JAVA_VERSION? -- some of the eclipse features may _silently_ fail. WARNING\!"
   # (if successful, the script is silent)
fi
