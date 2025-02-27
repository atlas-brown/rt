alias fw="sudo firewall-cmd"
alias fwp="sudo firewall-cmd --permanent"
alias fwr="sudo firewall-cmd --reload"
alias fwrp="sudo firewall-cmd --runtime-to-permanent"

function fwl () {
  # converts output to zsh array ()
  # @f flag split on new line
################################################################################
# Commit message: Fixed `fwl` function in `firewalld` plugin when `sources` used (#7011)  `firewall-cmd --get-active-zones` returns something like this:  ``` dmz   sources: ipset:dmz-hosts public   interfaces: eth0 ```  if zone binding is based on source ips, so strings with `sources: ...` should be excluded along with `interfaces: ...` to get zones list.
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/2b6434e8793a876e5465edd9c75819166878aba6
# Category: 
# Notes: 
# Changed content:
# -   zones=("${(@f)$(sudo firewall-cmd --get-active-zones | grep -v interfaces)}")
# +   zones=("${(@f)$(sudo firewall-cmd --get-active-zones | grep -v 'interfaces\|sources')}")
################################################################################
# put stream annotation here
# stream enable
  zones=("${(@f)$(sudo firewall-cmd --get-active-zones | grep -v interfaces)}")

  for i in $zones; do
    sudo firewall-cmd --zone $i --list-all
  done

  echo 'Direct Rules:'
  sudo firewall-cmd --direct --get-all-rules
}