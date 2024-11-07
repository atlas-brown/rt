#!/bin/bash
echo "=== CORPUS PIPELINE STARTED ==="
(cd original &&
 make python=python2 miniclean &&
 make python=python2 wips -B &&
 make python=python2 xmls -B) &&
make python=python2 annotations/fileids -B &&
make python=python2 vrt -j8 && make python=python2 installcorpus installtimespan installinfo
# ŭo
