#!/bin/bash
if [ $# -gt 1 ] #>
then
	echo "usage: $0 CMAKE_INSTALL_PREFIX(/usr/share etc..)"
	exit 1
fi


root=`pwd`
opt="/usr/local/TimePass"
if [ $# -eq 1 ]
then
	opt=${1}
fi

rm -rf ${opt}

cd ${root}"/example"
rm -rf build

cd ${root}"/src"
rm -rf build
