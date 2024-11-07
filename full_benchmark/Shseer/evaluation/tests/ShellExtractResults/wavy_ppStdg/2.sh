python get_version.py

NAME='WavyTool'
SYSTEM='linux'
VERSION=$(head -n 1 'got_version.temp')
DATE=`date +%Y%m%d%H%M`
EXECUTABLE=$NAME-$SYSTEM-portable-v.$VERSION-build.$DATE
$EXECUTABLE

rm -rfv 'got_version.temp'

cd ..

rm -rfv `find -iname "out.log*"`
rm -rfv `find -iname "*.spec"`
rm -rfv `find -iname "*pycache*"`
rm -rfv `find -iname "*.pyc"`
rm -rfv ./build
rm -rfv ./dist

pyinstaller ./run.py \
	--noconfirm \
	--clean \
	--log-level=INFO \
    --specpath=./dist \
	--name=$EXECUTABLE -F  \
	--icon=./wavytool/images/symbol.ico 


echo "Creating MD5 Checksum ..."
md5sum ./dist/$EXECUTABLE > ./dist/checksum.md5

echo "Creating list of imported library versions ..."
pip freeze > ./dist/lib_versions.info

echo "Compressing files ..."

cd ./dist
tar -cf - "$EXECUTABLE" "checksum.md5" "lib_versions.info" | gzip > "$EXECUTABLE.tar.gz"
cd ../scripts

echo "Process finished ..."


