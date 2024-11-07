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
roots=(${root}"/src" ${root}"/example")
for i in ${roots[@]}
do
	cd $i;
	if [ ! -d "build" ]
	then
		mkdir build;
	fi
	cd build;
	rm -rf *
	cmake -DCMAKE_INSTALL_PREFIX=${opt} ..
	make
	make install
done

export LD_LIBRARY_PATH=$opt:$LD_LIBRARY_PATH
