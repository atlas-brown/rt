#!/bin/sh

# input file (jo.??.in) is a shell script; the first line must
# be a comment and is used as the name of the test:
#
#		# basic logo
#		$JO -a jo
#
# the expect file (jo.??.exp) is a file which will be diff'd
# against the output of the corresponding .in file:
#
#		["jo"]
#


JO="$(pwd)/jo"
TESTDIR="${0%/*}"
NTESTS=$(expr $(ls $TESTDIR/jo.??.sh 2>/dev/null | wc -l))

export JO
export TESTDIR

echo "1..$NTESTS" # Number of tests to be executed.

n=0
for t in $TESTDIR/jo.??.sh; do
	n=$(expr $n + 1)
	input=$t
	expected="$TESTDIR/$(basename $t .sh).exp"
	output=$(mktemp /tmp/jo.XXXXXX)

	title=$(head -1 $input | sed -e 's/^#//')
	sh $input > $output
	RC=$?
	if [ $RC -ne 0 ]; then
		echo "not ok $n - $title"
		rm -f $output
		continue
	fi

	# if self-contained test (i.e. no 'expected' file exists)
	# use the previous RC
	if test -f "$expected"; then
		diff "$output" "$expected" > /dev/null
		RC=$?
	fi

	status="ok"
	if [ $RC -ne 0 ]; then
		status="not ok"
	fi

	echo "$status $n - $title"
	rm -f $output
done
