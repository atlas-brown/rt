#!/bin/bash
#' ---
#' title: Qualitas AG Hetzner Application Installation
#' date:  2020-05-06 17:11:33
#' author: Peter von Rohr
#' ---
#' ## Purpose
#' The required application should be installed and configured in a standard way.
#'
#' ## Description
#' Applications that are needed on the server are to be installed and configured. 
#' The applications are chosen from the definition file of the singularity 
#' container that is running on the Qualitas-ZWS servers.
#'
#' ## Details
#' The installed applications are the basic data-science tools. Specialised programs 
#' are copied from an existing server. The data-science tools are either installed 
#' using `apt` for all applications that are available in ubuntu repositories. 
#' All other tools are installed using a download with `curl`. The downloaded 
#' tar.gz-archives are extracted in a specific directory.
#'
#' ## Example
#' QSRCDIR=/home/quagadmin/source
#' QHTZDIR=${QSRCDIR}/quagzws-htz
#' if [ ! -d "$QSRCDIR" ]; then mkdir -p $QSRCDIR;fi
#' if [ ! -d "$QHTZDIR" ]; then 
#'   git -C "$QSRCDIR" clone https://github.com/pvrqualitasag/quagzws-htz.git
#' else
#'   git -C $QHTZDIR pull
#' fi
#' sudo su - -c "$QHTZDIR/bash/htz_install_app.sh"
#'
#' ## Set Directives
#' General behavior of the script is driven by the following settings
#+ bash-env-setting, eval=FALSE
set -o errexit    # exit immediately, if single command exits with non-zero status
set -o nounset    # treat unset variables as errors
set -o pipefail   # return value of pipeline is value of last command to exit with non-zero status
                  #  hence pipe fails if one command in pipe fails


#' ## Global Constants
#' ### Paths to shell tools
#+ shell-tools, eval=FALSE
ECHO=/bin/echo                             # PATH to echo                            #
DATE=/bin/date                             # PATH to date                            #
BASENAME=/usr/bin/basename                 # PATH to basename function               #
DIRNAME=/usr/bin/dirname                   # PATH to dirname function                #

#' ### Directories
#' Installation directory of this script
#+ script-directories, eval=FALSE
INSTALLDIR=`$DIRNAME ${BASH_SOURCE[0]}`    # installation dir of bashtools on host   #

#' ### Files
#' This section stores the name of this script and the
#' hostname in a variable. Both variables are important for logfiles to be able to
#' trace back which output was produced by which script and on which server.
#+ script-files, eval=FALSE
SCRIPT=`$BASENAME ${BASH_SOURCE[0]}`       # Set Script Name variable                #
SERVER=`hostname`                          # put hostname of server in variable      #



#' ## Functions
#' The following definitions of general purpose functions are local to this script.
#'
#' ### Usage Message
#' Usage message giving help on how to use the script.
#+ usg-msg-fun, eval=FALSE
usage () {
  local l_MSG=$1
  $ECHO "Usage Error: $l_MSG"
  $ECHO "Usage: $SCRIPT -q <server_fqdname> -l <local_app_dir>"
  $ECHO "  where -q <server_fqdname>  --  FQDNAME of server to be configured"
  $ECHO "        -l <local_app_dir>   --  remote directory including username usable with scp to be copied to new server (optional)"
  $ECHO ""
  exit 1
}

#' ### Start Message
#' The following function produces a start message showing the time
#' when the script started and on which server it was started.
#+ start-msg-fun, eval=FALSE
start_msg () {
  $ECHO "********************************************************************************"
  $ECHO "Starting $SCRIPT at: "`$DATE +"%Y-%m-%d %H:%M:%S"`
  $ECHO "Server:  $SERVER"
  $ECHO
}

#' ### End Message
#' This function produces a message denoting the end of the script including
#' the time when the script ended. This is important to check whether a script
#' did run successfully to its end.
#+ end-msg-fun, eval=FALSE
end_msg () {
  $ECHO
  $ECHO "End of $SCRIPT at: "`$DATE +"%Y-%m-%d %H:%M:%S"`
  $ECHO "********************************************************************************"
}

#' ### Log Message
#' Log messages formatted similarly to log4r are produced.
#+ log-msg-fun, eval=FALSE
log_msg () {
  local l_CALLER=$1
  local l_MSG=$2
  local l_RIGHTNOW=`$DATE +"%Y%m%d%H%M%S"`
  $ECHO "[${l_RIGHTNOW} -- ${l_CALLER}] $l_MSG"
}

#' ### Installation of Apt-Based Tools
#' Some data-science tools are available from ubuntu repositories. These are 
#' installed in the following function.
#+ apt-tools-install-fun
apt_tools_install () {
  # start with an updata/upgrade of the existing system
  apt update
  apt upgrade -y
  
  log_msg 'apt_tools_install' ' ** Add key and repo for R'
  # add key and repository for R
  apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9 
  add-apt-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu bionic-cran35/'
  apt update

  log_msg 'apt_tools_install' ' ** Install R, python and co ...'
  # install R, python and co.
  apt install -y r-base r-base-core r-recommended python python-pip python-numpy python-pandas python-dev python3-pip pandoc gnuplot 
  apt update
  apt upgrade -y
  
  log_msg 'apt_tools_install' ' ** Install R packages'
  R -e "install.packages(c('devtools', \
'remotes', \
'BiocManager', \
'doParallel', \
'e1071', \
'foreach', \
'gridExtra', \
'MASS', \
'plyr', \
'dplyr', \
'stringdist', \
'rmarkdown', \
'knitr', \
'tinytex', \
'openxlsx', \
'LaF', \
'reshape2', \
'data.table', \
'bit64', \
'tidyverse', \
'cowplot', \
'qqman', \
'svglite', \
'olsrr', \
'formatR', \
'pedigreemm', \
'xtable', \
'glmnet', \
'ISLR'), repos='https://cran.rstudio.com/', dependencies = TRUE)"
  
  log_msg 'apt_tools_install' ' ** Install pandas and numpy ...'
  # use pip to get numpy and pandas for py3
  /usr/bin/pip3 install pandas
  /usr/bin/pip3 install numpy
  
}

#' ### Installation of Tools with curl
curl_tools_install () {
  
  log_msg 'curl_tools_install' ' ** Install julia ...'
  # Install jula from download-host
  curl -sSL "https://julialang-s3.julialang.org/bin/linux/x64/1.1/julia-1.1.1-linux-x86_64.tar.gz" > julia.tar.gz 
  mkdir -p /opt/julia 
  tar -C /opt/julia -zxf julia.tar.gz 
  rm -f julia.tar.gz

  log_msg 'curl_tools_install' ' ** Install openjdk8 ...'
  # install OpenJDK 8 (LTS) from https://adoptopenjdk.net
  curl -sSL "https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/jdk8u222-b10/OpenJDK8U-jdk_x64_linux_hotspot_8u222b10.tar.gz" > openjdk8.tar.gz
  mkdir -p /opt/openjdk
  tar -C /opt/openjdk -xf openjdk8.tar.gz
  rm -f openjdk8.tar.gz
  
}


#' ### Installation of Local Tools
#' Local tools are installed based on an input file containing the locations from 
#' where the tools can be copied from
#+ local-tools-install-fun
local_tools_install () {
  local l_TOOSDIR=$1
  local l_LOCALDIR=$(echo $l_TOOSDIR | cut -d ':' -f 2)
  # check whether l_LOCALDIR exists
  if [ ! -d "$l_LOCALDIR" ];then 
    log_msg 'local_tools_install' ' ** Created $$l_LOCALDIR ...'
    mkdir -p $l_LOCALDIR
  fi
  log_msg 'local_tools_install' ' ** Installation of local tools from $l_TOOSDIR ...'
  scp -r $l_TOOSDIR $l_LOCALDIR 
}

#' ### Rstudio Server Installation
#' The rstudio server is installed
#+ rstudio-server-install-fun
rstudio_server_install () {
  log_msg 'rstudio_server_install' ' ** Installation of Rstudio server ...'
  # according to https://rstudio.com/products/rstudio/download-server/debian-ubuntu/
  apt update
  apt install -y gdebi-core
  # check whether rstudio server has already been installed
  if [ "$(service rstudio-server status 2> /dev/null | wc -l)" == "0" ]
  then
    wget https://download2.rstudio.org/server/bionic/amd64/rstudio-server-1.2.5042-amd64.deb
    gdebi --n rstudio-server-1.2.5042-amd64.deb
    rm rstudio-server-1.2.5042-amd64.deb
  else 
    log_msg 'rstudio_server_install' ' ** Rstudio server already seams to be installed...'
  fi
}

#' ### Shiny Server Installation
#' The shiny server is installed
#+ shiny-server-install-fun
shiny_server_install () {
  log_msg 'shiny_server_install' ' ** Installation of shiny server ...'
  
  # check whether rstudio server has already been installed
  if [ "$(service shiny-server status 2> /dev/null | wc -l)" == "0" ]
  then
    # according to https://rstudio.com/products/shiny/download-server/ubuntu/
    R -e "install.packages('shiny', repos='https://cran.rstudio.com/')"
    wget https://download3.rstudio.org/ubuntu-14.04/x86_64/shiny-server-1.5.13.944-amd64.deb
    gdebi --n shiny-server-1.5.13.944-amd64.deb
    rm shiny-server-1.5.13.944-amd64.deb
  else 
    log_msg 'shiny_server_install' ' ** Shiny server already seams to be installed...'
  fi
    
}

#' ### Nginx Configuration
#' The configuration of nginx is generated from a template
config_nginx () {
  log_msg 'config_nginx' ' ** Generate nginx from template ...'
  # check availablility of templated
  local l_NGINXTMPL=/home/quagadmin/source/quagzws-htz/input/nginx/n-htz_nginx.template
  if [ ! -d "$l_NGINXTMPL" ]; then usage " * ERROR: cannot find nginx-template: $l_NGINXTMPL";fi
  # generate nginx config file name from $FQDNAME
  local l_NGINXCONFIG=/etc/nginx/sites-enabled/$(echo $FQDNAME | cut -d '.' -f1)
  if [ -f "$l_NGINXCONFIG" ]
  then 
    log_msg 'config_nginx' ' * nginx config file already exists'
  else  
    # replace placeholder in template file
    log_msg 'config_nginx' ' ** Create nginx logfile from template ...'
    cat $l_NGINXTMPL | | sed -e "s/{FQDNAME}/$FQDNAME/" > $l_NGINXCONFIG
  fi  
  # check whether referenced certificates are available
  grep ssl_certificate $l_NGINXCONFIG | cut -d ' ' -f4 | sed -e 's/;//' | while read f
  do
    if [ -f "$f" ]
    then
      log_msg 'config_nginx' " ** Found certificate file: $f"
    else
      log_msg 'config_nginx' " * Cannot find $f -- RUN `letsencrypt certonly` to generate the certificates."
    fi
  done
  

}


#' ## Main Body of Script
#' The main body of the script starts here.
#+ start-msg, eval=FALSE
start_msg

#' ## Getopts for Commandline Argument Parsing
#' If an option should be followed by an argument, it should be followed by a ":".
#' Notice there is no ":" after "h". The leading ":" suppresses error messages from
#' getopts. This is required to get my unrecognized option code to work.
#+ getopts-parsing, eval=FALSE
FQDNAME=""
LOCALDIR=""
while getopts ":l:q:h" FLAG; do
  case $FLAG in
    h)
      usage "Help message for $SCRIPT"
      ;;
    l)
      LOCALDIR=$OPTARG
      ;;
    q)
      FQDNAME=$OPTARG
      ;;
    :)
      usage "-$OPTARG requires an argument"
      ;;
    ?)
      usage "Invalid command line argument (-$OPTARG) found"
      ;;
  esac
done

shift $((OPTIND-1))  #This tells getopts to move on to the next argument.

#' ## Checks for Command Line Arguments
#' The following statements are used to check whether required arguments
#' have been assigned with a non-empty value
#+ argument-test, eval=FALSE
if test "$FQDNAME" == ""; then
  usage "-q <server_fqdname> not defined"
fi


#' ## Apt-based Tools
#' In a first step, the tools available in ubuntu repositories are installed.
#+ apt-tools-install
log_msg "$SCRIPT" ' * Apt tools installation ...'
apt_tools_install


#' ## Curl-based Tools
#' Tools not available in an ubuntu repository are downloaded and installed.
log_msg "$SCRIPT" ' * Curl tools installation ...'
curl_tools_install


#' ## Local Tools Installation
#' Local tools are programs that are obtained or purchased and cannot be downloaded from 
#' anywhere. Hence they are just copied from an existing installation.
if [ "$LOCALDIR" != "" ]
then
  if [ -f "$LOCALDIR" ]
  then
    # installation of a list of local apps
    cat $LOCALDIR | while read f
    do
      log_msg "$SCRIPT" ' * Local tools installation of $f ...'
      local_tools_install $f
      sleep 2
    done
  else
    log_msg "$SCRIPT" ' * Local tools installation $LOCALDIR ...'
    local_tools_install $LOCALDIR
  fi  
fi

#' ## RStudio-Server
#' Installation of rstudio server
log_msg "$SCRIPT" ' * Install RStudio-server ...'
rstudio_server_install


#' ## Shiny Server
#' Installation of shiny server
log_msg "$SCRIPT" ' * Install shiny server ...'
shiny_server_install

#' ## Nginx Configuration
#' The nginx configuration is generated using a template
log_msg "$SCRIPT" ' * Configure nginx ...'
config_nginx


#' ## End of Script
#+ end-msg, eval=FALSE
end_msg

