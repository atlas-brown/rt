#!/bin/bash
set -e 

while getopts ":i:o:" opt; do
  case $opt in
    i) INPUT_FILE="$OPTARG"
    ;;
    o) MAPSFORGE_OPTIONS="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done


if [ "$INPUT_FILE" = "" ] ; then
  echo "Prepares an .osm for distribution with the ARIONAV framework."
  echo ""
  echo " -i <INPUT_FILE>"
  echo "    Mandatory input file parameter."
  echo ""
  echo " -o '<MAPSFORGE_OPTIONS>'"
  echo "    Optional arguments for the mapsforge file writer. Should be single-quoted."
  echo ""
  echo " -h"
  echo "    Prints this help."
  exit 1
fi

FULL_FILE_PATH=$(realpath $INPUT_FILE)
INPUT_FOLDER=$(dirname FULL_FILE_PATH)
NAME=$(basename $FULL_FILE_PATH)
NAME_WITHOUT_EXTENSION=${NAME::-4}
GH_FOLDER="$INPUT_FOLDER/${NAME_WITHOUT_EXTENSION}-gh/"
DISTRIBUTED_OSM_FILE="$GH_FOLDER/$NAME"




rm -rv ${GH_FOLDER}/*
java -jar $HOME/projects/graphhopper/level-extension-importer/target/level-extension-importer-0.5-jar-with-dependencies.jar $FULL_FILE_PATH $GH_FOLDER
echo "Executing SED to fix and copy osm file. May take a long time..."
date > SED.log
sed -E "s/node /node version='1' /" $FULL_FILE_PATH \
 | sed -E "s/way /way version='1' /" \
 | sed -E "s/relation /relation version='1' /" \
 | sed -E "s/(.*)version='1'(.*)version='(.*)'(.*)/\1 \2 version='\3'\4/" \
 | sed -E "s/.*tag(.*)v='.*version='1'.*'.*//" \
 > $DISTRIBUTED_OSM_FILE
date >> SED.log

date > $GH_FOLDER/_timestamp

echo "Creating mapsforge file with mapsforge options: '$MAPSFORGE_OPTIONS'"
osmosis --rx file="$DISTRIBUTED_OSM_FILE" enableDateParsing=false --mw $MAPSFORGE_OPTIONS file="$GH_FOLDER/${NAME_WITHOUT_EXTENSION}.map"

echo "Removing non-relevant data from distributed osm file..."
./bin/osmfilter32 "$DISTRIBUTED_OSM_FILE" --keep="name= and level= and indoor= or tourism=" > "${DISTRIBUTED_OSM_FILE}.indoor"
ls -lh ${GH_FOLDER}/${NAME}*
mv -v "${DISTRIBUTED_OSM_FILE}.indoor" "$DISTRIBUTED_OSM_FILE"


pushd $GH_FOLDER
  zip "${NAME_WITHOUT_EXTENSION}.ghz" *
  OUTPUT_FILE_FULL_PATH=$(realpath "${NAME_WITHOUT_EXTENSION}.ghz")
popd

echo "Output file is located at $OUTPUT_FILE_FULL_PATH"

