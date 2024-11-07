#!/bin/bash

function setCouplings () {
	COUPLING=$1
	VALUE=$2
	COUPSET=$3
	OUTFILE=$4

	for coupling in ${COUPSET[*]}
	do 
		if [ $coupling = $COUPLING ] ; then
			echo "	set $COUPLING $VALUE" >> $OUTFILE
		else
			echo "	set $coupling 0"      >> $OUTFILE
		fi
	done
	echo " 2 "	                      >> $OUTFILE

}

function setCuts () {
	OUTFILE=$1
	
	echo "set pta    15" >> $OUTFILE  
	echo "set ptl    20" >> $OUTFILE
	echo "set etaa  2.5" >> $OUTFILE
	echo "set etal  2.5" >> $OUTFILE
	echo "set drll  0.0" >> $OUTFILE
	echo "set dral  0.7" >> $OUTFILE
	echo "set mmll 50.0" >> $OUTFILE
}


COUPLING=$1
VALUE=$2
MGDIR=$3
OUTMG=$4
OUTCONF=$5
COUPSET=(CBtWL4 CBWL4 CWWL4 CBBL4)
if [ -z $COUPLING ] ; then
	echo "NTGC_generateMGFiles.sh: first input missing"
elif [ -z $VALUE ] ; then
	echo "NTGC_generateMGFiles.sh: second input missing"
else
	OUTNAME=${COUPLING}_${VALUE}
	OUTFILE=${OUTCONF}/mg5_${OUTNAME}.txt

	PROCESS="p p > z a, z > l- l+"

	################################################################
	echo "# Operationg for MadGraph NTGC" > $OUTFILE
	#echo "set lhapdf /cvmfs/cms.cern.ch/slc6_amd64_gcc700/cms/cmssw/CMSSW_10_2_13/external/slc6_amd64_gcc700/bin/lhapdf-config" >> $OUTFILE
	#echo "set fastjet $MGDIR/HEPTools/madanalysis5/madanalysis5/tools/fastjet/bin/fastjet-config" >> $OUTFILE
	#echo "set madanalysis-path $MGDIR/HEPTools/madanalysis5/madanalysis5/bin/ma" >> $OUTFILE
	if [ "$COUPLING" = "SMP" ] ; then 
		echo "import model sm"              >> $OUTFILE
	else
		echo "import model NTGC"              >> $OUTFILE
	fi
	echo "generate $PROCESS"              >> $OUTFILE
	echo "output ${OUTMG}/ntgc_llg_${OUTNAME}"     >> $OUTFILE
	if [ -d  "${OUTMG}/ntgc_llg_${OUTNAME}" ] ; then
		echo "y"                      >> $OUTFILE
	fi
	echo "launch"                         >> $OUTFILE
	echo "	0"                            >> $OUTFILE

	#setCouplings $COUPLING $VALUE $COUPET $OUTFILE
	for coupling in ${COUPSET[*]}
	do 
		if [ $coupling = $COUPLING ] ; then
			echo "	set $COUPLING $VALUE" >> $OUTFILE
		else
			echo "	set $coupling 0"      >> $OUTFILE
		fi
	done
	#echo " 2 "	                      >> $OUTFILE

	#setCuts $OUTFILE
	
	echo "set pta    15" >> $OUTFILE  
	echo "set ptl    20" >> $OUTFILE
	echo "set etaa  2.5" >> $OUTFILE
	echo "set etal  2.5" >> $OUTFILE
	echo "set drll  0.0" >> $OUTFILE
	echo "set dral  0.7" >> $OUTFILE
	echo "set mmll 50.0" >> $OUTFILE

	echo " 0 "	                      >> $OUTFILE
fi


