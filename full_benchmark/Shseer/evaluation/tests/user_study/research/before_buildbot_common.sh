#!/bin/bash -e

# where is this script?
if [ -z ${scriptdir} ] ; then
    scriptdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
fi

if [ -z ${buildtype} ] ; then
    buildtype=RelWithDebInfo
fi

if [ -z ${myarch} ] ; then
    echo "myarch is not set. Please source the appropriate settings in the ${scriptdir} directory.";
    kill -INT $$

fi

export nprocs=2
osname=`uname`
if [ ${osname} == "Darwin" ]; then
    nprocs=`sysctl -n hw.ncpu`
    ntcores=`sysctl -n hw.ncpu`
else
    nprocs=`nproc --all`
    # Get the true number of total cores, not threads.
    ncores=`lscpu | grep -E '^Core' | awk '{print $NF}'`
    nsockets=`lscpu | grep -E '^Socket' | awk '{print $NF}'`
    let ntcores=$ncores*$nsockets
fi

# be a good citizen. ;)
# There will be 3 concurrent builds, so use less than 1/3 of the cores.
# Delphi should be < 9
# Centaur should be < 5
# Grover should be < 17
let max_load=$ntcores
let max_jobs=$ntcores/2

# laptops and so forth can go full steam ahead...
if [ $nprocs -lt 16 ] ; then
    let max_load=$ntcores
    let max_jobs=$ntcores/2
fi

makej="-j ${max_jobs} -l ${max_load}"
#export CTEST_PARALLEL_LEVEL=${max_jobs}
#export HPX_COMMANDLINE_OPTIONS=--hpx:bind=none

# Assume that the buildbot script directory is in phylanx/tools/buildbot
# of the phylanx project.
tmptop=$( dirname "${scriptdir}" )
top=${tmptop}/buildbot
sourcedir=${top}/src
buildprefix=${top}/build-${myarch}

# Assume that the buildbot script directory is in phylanx/tools/buildbot
# of the phylanx project. We need to go up one more directory to get
# to the project root directory.
phylanx_src_dir=$( dirname "${tmptop}" )
phylanx_build_dir=${buildprefix}/phylanx-${buildtype}
phylanx_install_dir=${buildprefix}/phylanx-${buildtype}-install

pybind_src_dir=${sourcedir}/pybind11-2.2.2
pybind_build_dir=${buildprefix}/pybind-${buildtype}

eigen_src_dir=${sourcedir}/eigen-eigen-5a0156e40feb
eigen_build_dir=${buildprefix}/eigen3-${buildtype}

blaze_src_dir=${sourcedir}/blaze-head
blaze_build_dir=${buildprefix}/blaze-${buildtype}

blazetensor_src_dir=${sourcedir}/blaze_tensor
blazetensor_build_dir=${buildprefix}/blaze_tensor-${buildtype}

high5_src_dir=${sourcedir}/HighFive-1.5
high5_build_dir=${buildprefix}/high5-${buildtype}

hpx_src_dir=${sourcedir}/hpx
HPX_ROOT=${buildprefix}/hpx-${buildtype}

# go up one directory
basedir=$(dirname ${scriptdir})
echo "Basedir: ${basedir}"
