#!/bin/bash
red="\e[31m"
green="\e[32m"
blue="\e[34m"
normal="\e[0m"
bold="\e[1m"

DIR_PROJECT=$(cd $(dirname $BASH_SOURCE[0]) && pwd)

if [ $# -lt 3 ]; then
    echo -e $red"GenerateCpp.sh needs more parameters"$normal
    echo -e $red"./GenerateCpp.sh build config_file prefix"$normal
    exit 1
fi

BUILD=$1
CONFIG_FILE=$2
PREFIX=$3
CPPFILE=$BUILD"/"$PREFIX".cpp"
HEAD=$DIR_PROJECT"/Head"
EXTRACT="InitGenData/ExtractConfig.sh"
MAINHEAD=$DIR_PROJECT"/MainHead"
MAINMEDIUM=$DIR_PROJECT"/MainMedium"
MAINTAIL=$DIR_PROJECT"/MainTail"
VARIABLES=($(cat $CONFIG_FILE | grep "names@" | cut -d"@" -f 2))
VARNUM=${#VARIABLES[@]}

#---------------------------------------------
## Extract function from config file
#---------------------------------------------
./$EXTRACT $BUILD $CONFIG_FILE $CPPFILE

#---------------------------------------------
## Cat main function
#---------------------------------------------
cat $MAINHEAD >> $CPPFILE
for i in "${VARIABLES[@]}"
do
    printf "\t\tp->%s = (rand() %% 201 ) - 100;\n" $i >> $CPPFILE
done
printf "\n" >> $CPPFILE
cat $MAINMEDIUM >> $CPPFILE
for (( i=0; i<${VARNUM}-1; i++  ));
do
    printf "\t\tcout << \"%d:\" << positiveSet[i].%s << \" \";\n" $[i + 1] ${VARIABLES[$i]} >> $CPPFILE
done
printf "\t\tcout << \"%d:\" << positiveSet[i].%s << \" \" << endl;\n" ${VARNUM} ${VARIABLES[(( $VARNUM - 1 ))]} >> $CPPFILE

printf "\t}\n\tfor(size_t i = 0;i < negativeSet.size();i++){\n\t\tcout << \"-1 \";\n" >> $CPPFILE
for (( i=0; i<${VARNUM}-1; i++  ));
do
    printf "\t\tcout << \"%d:\" << negativeSet[i].%s << \" \";\n" $[i + 1] ${VARIABLES[$i]} >> $CPPFILE
done
printf "\t\tcout << \"%d:\" << negativeSet[i].%s << \" \" << endl;\n" ${VARNUM}  ${VARIABLES[(( $VARNUM - 1 ))]} >> $CPPFILE
cat $MAINTAIL >> $CPPFILE
