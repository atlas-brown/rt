#!/bin/sh
#
# Make a Rocket image tree for mongodb
#
SOURCE=""
DEST=image/rootfs
BINFILES="/usr/bin/bash /usr/bin/ls /usr/bin/env /usr/bin/find"
#CONFIGFILE=/etc/mongodb.conf

mkdir -p ${DEST}
mkdir -p ${DEST}/lib64
mkdir -p ${DEST}/usr/bin
#mkdir -p ${DEST}/etc
#mkdir -p ${DEST}/proc

for BINFILE in ${BINFILES}
do
	        echo -n "${BINFILE} " && rpm -qf ${BINFILE}
		cp ${BINFILE} ${DEST}${BINFILE}
		chmod a+x ${DEST}${BINFILE}
		SHAREDOBJS=$(ldd ${BINFILE} | awk '{print $1}' | grep -e ^/)
		for SOFILE in ${SHAREDOBJS}
		do
	                        echo -n "${SOFILE} " && rpm -qf ${SOFILE}
				cp ${SOFILE} ${DEST}${SOFILE}
		done
		SHAREDOBJS=$(ldd ${BINFILE} | awk '{print $3}' | grep -e ^/lib)
		for SOFILE in ${SHAREDOBJS}
		do
	                        echo -n "${SOFILE} " && rpm -qf ${SOFILE}
				cp ${SOFILE} ${DEST}${SOFILE}
		done
		
done

#cp ${CONFIGFILE} ${DEST}${CONFIGFILE}
cp run.sh ${DEST}/run.sh
chmod a+x ${DEST}/run.sh

cp manifest image
