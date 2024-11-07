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
PRECONDITION=$(cat $CONFIG_FILE | grep "precondition@" | cut -d"@" -f 2)

#---------------------------------------------
## Extract function from config file
#---------------------------------------------
./$EXTRACT $BUILD $CONFIG_FILE $CPPFILE

#---------------------------------------------
## GiveVarValue function
#---------------------------------------------
printf "void GiveVarValue(Node *p, z3::func_decl v, z3::model m) {\n\tint val = m.get_const_interp(v).get_numeral_int();\n\tstring name = v.name().str();\n" >> $CPPFILE
printf "\tif(name == \"%s\") p->%s = val;\n" ${VARIABLES[0]} ${VARIABLES[0]} >> $CPPFILE
for (( i=1; i<$VARNUM; i++  ));
do
    printf "\telse if(name == \"%s\") p->%s = val;\n" ${VARIABLES[$i]} ${VARIABLES[$i]} >> $CPPFILE
done
printf "\telse {\n\t\tcerr << \"There's something wrong in GiveVarValue function\" << endl;\n\t\texit(-1);\n\t}\n}\n\n" >> $CPPFILE

#---------------------------------------------
## Cat main function
#---------------------------------------------
cat $MAINHEAD >> $CPPFILE

#---------------------------------------------
# Using SMT to solve the precondition
#---------------------------------------------
for i in "${VARIABLES[@]}"
do
    printf "\tz3::expr %s = c.int_const(\"%s\");\n" $i $i >> $CPPFILE
done
printf "\n\tz3::solver s(c);\n\n\t// precondition\n" >> $CPPFILE
printf "\ts.add(%s);\n\n" "$PRECONDITION" >> $CPPFILE
printf "\tswitch(s.check()) {\n\t\tcase z3::unsat: return -1; break;\n\t\tcase z3::sat: {\n\t\t\tz3::model m = s.get_model();\n\t\t\tNode *p = new Node;\n\t\t\tz3::func_decl v = m[0];\n" >> $CPPFILE
printf "\t\t\tGiveVarValue(p, v, m);\n" >> $CPPFILE
for (( i=1; i<$VARNUM; i++  ));
do
    printf "\t\t\tv = m[%d];\n" $i >> $CPPFILE
    printf "\t\t\tGiveVarValue(p, v, m);\n" >> $CPPFILE
done
printf "\t\t\tGetPositive(p, positiveSet);\n\t\t\tbreak;\n\t\t}\n\t\tcase z3::unknown: return -1;break;\n\t}\n\n\ts.reset();\n\n\t// !precondition\n" >> $CPPFILE
printf "\ts.add(!(%s));\n\n" "$PRECONDITION" >> $CPPFILE
printf "\tswitch(s.check()) {\n\t\tcase z3::unsat: return -1; break;\n\t\tcase z3::sat: {\n\t\t\tz3::model m = s.get_model();\n\t\t\tNode *p = new Node;\n\t\t\tz3::func_decl v = m[0];\n" >> $CPPFILE
printf "\t\t\tGiveVarValue(p, v, m);\n" >> $CPPFILE
for (( i=1; i<$VARNUM; i++  ));
do
    printf "\t\t\tv = m[%d];\n" $i >> $CPPFILE
    printf "\t\t\tGiveVarValue(p, v, m);\n" >> $CPPFILE
done
printf "\t\t\tGetNegative(p, negativeSet);\n\t\t\tbreak;\n\t\t}\n\t\tcase z3::unknown: return -1;break;\n\t}\n\n\tsrand((int)time(0));\n\twhile(positiveSet.size() <= 10 || negativeSet.size() <= 10) {\n\t\tNode *p = new Node;\n" >> $CPPFILE

#---------------------------------------------
# Using random to add more data
#---------------------------------------------
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
