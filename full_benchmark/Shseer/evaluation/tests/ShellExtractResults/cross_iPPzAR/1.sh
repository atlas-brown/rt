#!/bin/sh
#For wisdom look here: http://qt-project.org/wiki/Building_Qt_5_from_Git
#For filthy automation look here

#Die (painfully!) on error
set -e

if [ "$#" -lt 1 ]; then
    echo 'Need at least one argument built-qt5 $prefix foo'
    exit -1
fi

if [ -z "$QT5BASE" ]; then
	echo "QT5BASE env variable must be set prior to running this script"
	exit -1
fi

function build {
    echo "Building $1"
    BUILD_PATH="$QT_BUILD_DIR/work/$1"
    mkdir -p $BUILD_PATH
    cd $BUILD_PATH
    $PREFIX/bin/qmake "$QT5BASE/$1/$1.pro"
    make
    make install
}

PREFIX=$1
CONFIGURE_OPTIONS=$2
BUILD_TYPE=$3
ADDITIONAL_MODULES=$4

if [ "$PREFIX" = "." ]; then
    PREFIX=$PWD
fi

if [ -z "$QT_BUILD_DIR" ]; then
    QT_BUILD_DIR=$PREFIX
fi

export QTDIR=$PREFIX

mkdir -p $QT_BUILD_DIR/work/qtbase
cd $QT_BUILD_DIR/work/qtbase

echo "Configuring Qt with $CONFIGURE_OPTIONS"
#-separate-debug-info -useful- reintroduce
$QT5BASE/qtbase/configure -opensource -confirm-license -optimized-qmake \
                          -reduce-relocations -reduce-exports \
                          -release -make libs -prefix $PREFIX \
                          $CONFIGURE_OPTIONS
make
make install

if [ "$BUILD_TYPE" = "all" ]; then
MODULES="qtimageformats qtsvg qtjsbackend qtscript qtxmlpatterns qtdeclarative qtsensors qt3d qtgraphicaleffects qtjsondb qtlocation qtdocgallery"
elif [ "$BUILD_TYPE" = "minimal" ]; then
MODULES="qtjsbackend qtxmlpatterns qtdeclarative"
else
MODULES="qtsvg qtimageformats qtjsbackend qtscript qtdeclarative qtsensors qt3d qtgraphicaleffects"
fi

echo "Building: $MODULES"

for module in $MODULES
do
    build "$module"
done

echo "Building $ADDITIONAL_MODULES"

for module in $ADDITIONAL_MODULES
do
    build "$module"
done

echo "Time to die"
#Webkit is septic at present
exit 0

BUILD_PATH="$QT_BUILD_DIR/work/qtwebkit"
mkdir -p $BUILD_PATH
cd $BUILD_PATH

export WEBKITOUTPUTDIR=$PWD/WebKitBuild
perl $QT5BASE/qtwebkit/Tools/Scripts/build-webkit --qt --qmake=$PREFIX/bin/qmake --install-libs=$PREFIX --release --no-webgl --no-3d-rendering --no-svg

echo "Time to die peacefully"
