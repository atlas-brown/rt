#!/bin/bash

export QUERY_STRING="a&c=1&d=2&d=3&do_ajax"

WPL="/usr/bin/wpl";
TMP="tmp_test";

if [ ! -f $WPL ]; then
	echo "Could not find wrapper script for WPL-executable"
	exit 1
fi

SOMETHING_WENT_WRONG=0

# Generate .result-files if they don't already exist
for FILE in `ls *.pstar`; do
	RESULT_FILE="$FILE.result";
	if [ ! -f "$RESULT_FILE" ]; then
		echo -n "Generate $FILE...";
		$WPL -f $FILE > $RESULT_FILE;
		if [ "$?" != "0" ]; then
			echo "Error when generating result file for script '$FILE'"
			exit 1
		fi
		echo "Done";
	fi
	echo -n "Checking $FILE...";

	$WPL -f $FILE 2>&1 > $TMP;
	if [ "$?" != "0" ]; then
		echo "failed 1";
		SOMETHING_WENT_WRONG=1
	else
		cmp -s $TMP $RESULT_FILE 2>&1 
		if [ "$?" != "0" ]; then
			echo "failed 2";
			SOMETHING_WENT_WRONG=1
		else
			echo "OK";
		fi
	fi
done

rm $TMP

if [ "$SOMETHING_WENT_WRONG" == "0" ]; then
	echo "All good"
else
	echo "Something went wrong"
fi

exit $SOMETHING_WENT_WRONG
