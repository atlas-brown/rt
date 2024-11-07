#!/bin/sh
# Check if the rSON directory is valid or not
if [ ! -d rSON ]; then
	echo "Downloading rSON...."
	# And get Git to grab rSON from the remote if not
	if !(git submodule init) || !(git submodule update); then
		echo "Error downloading rSON.."
		exit 1
	fi
fi

# Runs a compile and link test run
buildTest()
{
	rm -f buildtest
	if
	{
		(exec $CXX -lrSON -o buildtest buildtest.cpp) 2> buildtest.err
		status=$?
		if test -s buildtest.err; then
			grep -v '^ *+' buildtest.err > buildtest.er1
			mv -f buildtest.er1 buildtest.err
		fi
		test $status = 0;
	} && test ! -s buildtest.err && test -s buildtest; then
		status=0
	else
		status=1
	fi
	rm -f buildtest buildtest.cpp buildtest.err
	return $status
}

# Check for the exists() function which is needed by IRCBot and was added
# since IRCBot was created.
echo -n "Checking for rSON::JSONObject::exists().... "
cat - <<EOF > buildtest.cpp
#include <rSON.h>
using namespace rSON;

int main(int, char **)
{
	JSONObject obj;
	obj.exists("test");
	return 0;
}
EOF
# Do a barrel roll
eval "status=buildTest";
if $status; then
	echo "yes"
else
	echo "no"
	# Roll failed (exists() does not exist, or rSON not installed)
	# so unset the MAKEFLAGS variable to prevent incorrect function of rSON's makefile
	unset MAKEFLAGS
	unset MFLAGS
	# Enable exit on error
	set -e
	cd rSON
	# And compile rSON and install it.
	make GCC="$GCC -fPIC -DPIC" LIBDIR=$LIBDIR
	sudo make install GCC="$GCC -fPIC -DPIC" LIBDIR=$LIBDIR
fi

