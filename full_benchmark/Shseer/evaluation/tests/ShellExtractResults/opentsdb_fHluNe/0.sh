if [ "$1x" == "x" ]; then
   echo "Usage: $0 path-to-opentsdb-builddir"
   exit 1
fi
mvn install:install-file  -Dfile=$1/target/opentsdb-2.1.3.jar \
                          -Dsources=$1/target/opentsdb-2.1.3-sources.jar \
                          -DpomFile=$1/pom.xml \
                          -DlocalRepositoryPath=repo
