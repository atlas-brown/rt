#xc function courtesy of http://gist.github.com/subdigital/5420709
function xc {
################################################################################
# Commit message: use ls instead of find to avoid incompatibility with gnu find
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/3cdfdad28a1b7efbcc1cd1282e7811d80f50a730
# Category: 
# Notes: 
# Changed content:
# - xcode_proj=`find . -name "*.xc*" -d 1 | sort -r | head -1`
# + xcode_proj=`ls | grep "\.xc" | sort -r | head -1`
################################################################################
# put stream annotation here
# stream enable
  xcode_proj=`ls | grep "\.xc" | sort -r | head -1`
  if [[ `echo -n $xcode_proj | wc -m` == 0 ]]
  then
    echo "No xcworkspace/xcodeproj file found in the current directory."
  else
    echo "Found $xcode_proj" 
    open "$xcode_proj" 
  fi
}

function xcsel {
  sudo xcode-select --switch "$*"
}

alias xcb='xcodebuild'
alias xcp='xcode-select --print-path'
alias simulator='open $(xcode-select  -p)/Platforms/iPhoneSimulator.platform/Developer/Applications/iPhone\ Simulator.app'