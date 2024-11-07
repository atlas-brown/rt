#!/bin/sh
#
# Make a Rocket image tree for mongodb
#
SOURCE=""
DEST=image/rootfs
BINFILES="/usr/bin/python"
PYLIBDIR=/usr/lib64/python2.7
PYLIBEXECDIR=${PYLIBDIR}/lib-dynload
PYMODULES="site os posixpath stat genericpath warnings linecache types
UserDict _abcoll abc _weakrefset copy_reg traceback sysconfig 
re sre_compile sre_parse sre_constants
_sysconfigdata
"

mkdir -p ${DEST}
mkdir -p ${DEST}/lib64
mkdir -p ${DEST}/usr/bin
mkdir -p ${DEST}${PYLIBDIR}
mkdir -p ${DEST}${PYLIBEXECDIR}
# /usr/lib64/python2.7/plat-linux2


for BINFILE in ${BINFILES}
do
	  echo -n "${BINFILE} " && rpm -qf --qf "%{NAME}\n" ${BINFILE}
		cp ${BINFILE} ${DEST}${BINFILE}
		chmod a+x ${DEST}${BINFILE}
		SHAREDOBJS=$(ldd ${BINFILE} | awk '{print $1}' | grep -e ^/)
		for SOFILE in ${SHAREDOBJS}
		do
	      echo -n "${SOFILE} " && rpm -qf --qf "%{NAME}\n" ${SOFILE}
				cp ${SOFILE} ${DEST}${SOFILE}
		done
		SHAREDOBJS=$(ldd ${BINFILE} | awk '{print $3}' | grep -e ^/lib)
		for SOFILE in ${SHAREDOBJS}
		do
	      echo -n "${SOFILE} " && rpm -qf ${SOFILE}
				cp ${SOFILE} ${DEST}${SOFILE}
		done
done

for MODULE in ${PYMODULES}
do
		PYCFILE=${PYLIBDIR}/${MODULE}.pyc
		echo -n "${PYCFILE} " && rpm -qf --qf "%{NAME}\n" ${PYCFILE} 
		cp ${PYLIBDIR}/${MODULE}.pyc ${DEST}/${PYLIBDIR}/${MODULE}.pyc
done

#cp ${CONFIGFILE} ${DEST}${CONFIGFILE}
cp run.py ${DEST}/run.py
chmod a+x ${DEST}/run.py

cp manifest image
