#!/bin/bash

# This script assumes that you are running maven-3.6.3 or above, please refer to http://maven.apache.org/guides/getting-started/maven-in-five-minutes.html for more information.

if [ $# -ne 1 ]; then   
  echo "Usage: $0 <operation code, e.g. \"create_subprojects\" or \"exec_arithmetics\">"   
  exit 1 
fi

basedir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

groupId=com.mycompany.app
hybridGroupId=com.mycompany.hybrid
archetypeArtifactId=maven-archetype-quickstart
archetypeVersion=1.4

hybridArtifactId=hybrid
arithmeticsArtifactId=arithmetics
stringhelperArtifactId=stringhelper

function package_every_subproject_individually() {
  subprojects=( $arithmeticsArtifactId $stringhelperArtifactId )
  for i in "${subprojects[@]}"
  do
    if [[ -d $basedir/$i ]]; then
      echo "Packaging subproject $i"
      cd $basedir/$i && mvn clean -DskipTests && mvn package -DskipTests
    fi
  done
}

function package_wrapped_hybrid() {
  echo "Packaging the wrapped hybrid"
  cd $basedir && mvn clean -DskipTests && mvn package -DskipTests -P shading 
  subprojects=( $arithmeticsArtifactId $stringhelperArtifactId )
  for i in "${subprojects[@]}"
  do
    if [[ -d $basedir/$i ]]; then
      echo "Deploying built target of subproject $i (shaded)"
      # A "$basedir/snapshot-repo" is used in this project to avoid installing experimental jars into the OS-scope maven repo, e.g. $HOME/.m2/repository. 
      cd $basedir/$i && mvn deploy -DskipTests -P shading 
    fi
  done
}

function exec_hybrid() {
  if [[ -d $basedir/$hybridArtifactId ]]; then
    echo "Executing hybrid"
    cd $basedir/$hybridArtifactId && mvn exec:java -Dexec.mainClass="$hybridGroupId.HybridApp" #-Dexec.args="argument1" ...
  fi
}

function exec_arithmetics() {
  if [[ -d $basedir/$arithmeticsArtifactId ]]; then
    echo "Executing subproject $arithmeticsArtifactId (NOT shaded)"
    cd $basedir/$arithmeticsArtifactId && mvn clean package -DskipTests && mvn exec:java -Dexec.mainClass="$groupId.App" #-Dexec.args="argument1" ...
  fi
}

function exec_stringhelper() {
  if [[ -d $basedir/$stringhelperArtifactId ]]; then
    echo "Executing subproject $stringhelperArtifactId (NOT shaded)"
    cd $basedir/$stringhelperArtifactId && mvn clean package -DskipTests && mvn exec:java -Dexec.mainClass="$groupId.App" #-Dexec.args="argument1" ...
  fi
}

function create_subprojects () {
  subprojects=( $arithmeticsArtifactId $stringhelperArtifactId )
  for i in "${subprojects[@]}"
  do
    if [[ ! -d $basedir/$i ]]; then
      echo "Creating subproject $i"
      cd $basedir && mvn -X archetype:generate -DgroupId=$groupId -DartifactId=$i -DarchetypeArtifactId=$archetypeArtifactId -DarchetypeVersion=$archetypeVersion -DinteractiveMode=false
    fi
    cp $basedir/pom-file-templates/$i-pom.xml $basedir/$i/pom.xml 
  done

  if [[ ! -d $basedir/$hybridArtifactId ]]; then
    cd $basedir && mvn -X archetype:generate -DgroupId=$hybridGroupId -DartifactId=$hybridArtifactId -DarchetypeArtifactId=$archetypeArtifactId -DarchetypeVersion=$archetypeVersion -DinteractiveMode=false
  fi
  cp $basedir/pom-file-templates/$hybridArtifactId-pom.xml $basedir/$hybridArtifactId/pom.xml 

  cp $basedir/pom-file-templates/root-pom.xml $basedir/pom.xml 
}

operationCode=$1
$operationCode
