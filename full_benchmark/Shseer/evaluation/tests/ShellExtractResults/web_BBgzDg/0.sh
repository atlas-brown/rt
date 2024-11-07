#!/bin/bash

draft=$1

set -e

kramdown-rfc2629 $draft.md > $draft.xml

xml2rfc --text $draft.xml
xml2rfc --html $draft.xml

        

