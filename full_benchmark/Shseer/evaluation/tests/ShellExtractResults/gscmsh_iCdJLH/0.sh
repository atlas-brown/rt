#!/bin/sh

#Here be constants
TEMPDIR="/tmp/getSimpleCMSsetup" #The name of the temporary dir. For actual use call createTempDir, which appends a unix timestap to ensure collison prevention

#--------------------------Function Definitions--------------------------------#

#creates a temporary directory and writes its path to the stdout
createTempDir() {
  dir=$TEMPDIR$(date +"%s")
  echo $dir
}

#checks if $1 is the GetSimple CMS top level directory with the plugins and theme folders in it 
isWebsiteRootDirectory() {
  if [ -n "$(ls $1 | grep plugins)" ] && [ -n "$(ls $1 | grep theme)" ]; then  
    return 0
  else 
    return 1
  fi
}

#iteratively check directories up to the root direcotry of the site
#if used withe the --check option, it does not write to stdout, but 
#only determines, if the script has been called from within a valid directory
getWebsiteRootDirectory() {
  #dir is the directory to start in
  dir="./" 

  while ! isWebsiteRootDirectory $dir; do
    dir=$dir"../"
    #if root of filesystem has been reached exit with error status
    if [ "$(realpath $dir)" = "/" ]; then
      exit 1
    fi
  done
  
  if [ "$1" != "--check" ]; then
    echo "$dir"
  fi 
  
  exit 0
}

installPlugin() {
  zipfile=$(basename "$1")
  
  #switch to the plugin directory
  cd $(getWebsiteRootDirectory)"plugins"
  
  #download and install the plugin
  wget $1
  
  #TODO: Make sure that plugin zips are, in contrast to themes, consistently structured (compare line 59)
  unzip $zipfile
  rm $zipfile  
  
  #return to former directory
  cd $OLDPWD
}

installTheme() {
  zipfile=$(basename "$1")
  
  #switch to the theme directory
  cd $(getWebsiteRootDirectory)"theme"
  
  wget $1
  #some zips can be directly unzipped, others must be extracted into an extra directory. User intervention necessary.
  #TODO: Automate the detection of toplevelfolder within the archive and only ask for name if necessary
  unzip -l $zipfile  
  echo "If the content of the zip is organised under one subdirectory press Enter. Otherwise enter a name for the theme: "
  read input
  
  if [ -z "$input" ]; then
    #input empty, assuming, that the zipfile has to be extracted only
    unzip $zipfile
  else
    #create directory with name entered
    mkdir $input
    unzip $zipfile -d $input
  fi
  
  rm $zipfile
  
  #return to former directory
  cd $OLDPWD   
}

removePlugin() {
  echo "Warning: This will remove $1 from the filesystem. Do you want to continue? [y/N]"
  
  read input
  if [ $input = y ] || [ $input = Y ]; then
    #only remove, after confirmation, to avoid accidental removes
    dir=$(getWebsiteRootDirectory)
    rm $dir"plugins/"$1".php"
    
    #if the plugin came with a directory of assets, also delete this
    if [ -e $dir"plugins/"$1 ]; then
      rm -r $dir"plugins/"$1 
    fi
  fi
}

#Lists all installed Plugins
#TODO: Display description and active status
listPlugins() {
  dir=$(getWebsiteRootDirectory)"plugins/"
  pluginfiles=$(ls $dir| grep ".php")
  echo "Your currently installed plugins are as follows:"
  echo " "$pluginfiles | sed 's/.php/\n/g'
}

listThemes() {
  dir=$(getWebsiteRootDirectory)"theme"
  themefiles=$(ls $dir)
  echo "Your currently installed themes are as follows:"
  for theme in $themefiles; do
    echo " "$theme
  done
}

#downloads the latest version of GetSimple CMS and unzips it
setupCMS() {
  name=$1
  if [ -z "$name" ]; then
    #if empty, prompt for name
    echo "What do you want the website's folder to be named like?"
    read name
  fi
  
  if [-z "$name" ]; then
    echo "No proper name entered. Aborting..."
    exit 1
  fi
  
  #if proper name has been entered, begin the actual process
  #create tmp directory
  tmp=$(createTempDir)
  #download and unzip it there
  wget -P $tmp http://get-simple.info/latest
  unzip $tmp"/latest" -d $tmp
  
  #this is the name of the file inside of the zip archive. As there is a varying
  #version number, I figure out the complete filename with a "ls | grep"
  originalName=$(ls $tmp | grep GetSimple)
  
  #move the subfolder, containing the actual GetSimple CMS Installation
  mv "$tmp/$originalName" $name
  
  echo "$originalName has been installed to $name"
  
  rm -r $tmp
}

#Activates a plugin
activatePlugin() {
  file=$(getWebsiteRootDirectory)"data/other/plugins.xml"
  search='<item><plugin><!\[CDATA\['$1'.php\]\]><\/plugin><enabled><!\[CDATA\[false\]\]><\/enabled><\/item>'
  replace='<item><plugin><!\[CDATA\['$1'.php\]\]><\/plugin><enabled><!\[CDATA\[true\]\]><\/enabled><\/item>'
  sed -i "s/$search/$replace/" $file
}

#Deactivates a plugin
deactivatePlugin() {
  file=$(getWebsiteRootDirectory)"data/other/plugins.xml"
  search='<item><plugin><!\[CDATA\['$1'.php\]\]><\/plugin><enabled><!\[CDATA\[true\]\]><\/enabled><\/item>'  
  replace='<item><plugin><!\[CDATA\['$1'.php\]\]><\/plugin><enabled><!\[CDATA\[false\]\]><\/enabled><\/item>'
  sed -i "s/$search/$replace/" $file
}

#Flushes the Websites Cache
flushCache() {
  dir=$(getWebsiteRootDirectory)"data/cache"
  rm -rf $dir/*
}

#---------------------This is where the actual execution begins-----------------------#

#check if script has been called from within a Get Simple CMS installation directory
if ! $(getWebsiteRootDirectory --check); then
  echo "This script must be called from within a proper installation directory of GetSimple CMS.
Do you want to create one here? [y/N]"
  read input
  if [ $input = y ] || [ $input = Y ]; then
    setupCMS
  fi
  exit 1
fi

case "$1" in
  "pinstall")  installPlugin $2
  ;;
  "tinstall") installTheme $2
  ;;
  "premove") removePlugin $2
  ;;
  "penable") activatePlugin $2
  ;;
  "pdisable") deactivatePlugin $2
  ;;
  "plist") listPlugins
  ;;
  "tlist") listThemes
  ;;
  "flush") flushCache
  ;;
  *) echo "Usage: $(basename $0) <action> [<parameters>]
  Possible actions are:
    pinstall <URL> - Install a Plugin
    tinstall <URL> - Install a Theme
    premove <NAME> - Remove a Plugin
    penable <NAME> - Activates a Plugin
    pdisable <NAME> - Deactivates a Plugin
    plist - List Plugins installed
    tlist - List Themes installed
    flush - Flushes the Cache
    
  Where <URL> stands for an URL pointing to the zip of the plugin or script as can be found on http://get-simple.info/extend/"
  ;;
esac
