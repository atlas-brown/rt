############################################################
# Take all host sections in .ssh/config and offer them for
# completion as hosts (e.g. for ssh, rsync, scp and the like)
# Filter out wildcard host sections.
_ssh_configfile="$HOME/.ssh/config"
if [[ -f "$_ssh_configfile" ]]; then
################################################################################
# Commit message: fix(ssh): allow multiple definitions per host (#12227)
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/50fd98e5a6c9d7c36b0cc678f577f7ce1d181bea
# Category: hard awk
# Notes: 
# Changed content:
# -   _hosts=($(egrep '^Host.*' "$_ssh_configfile" | awk '{print $2}' | grep -v '^*' | sed -e 's/\.*\*$//'))
# -   zstyle ':completion:*:hosts' hosts $_hosts
# -   unset _hosts
# +   _ssh_hosts=($(
# +     egrep '^Host.*' "$_ssh_configfile" |\
# +     awk '{for (i=2; i<=NF; i++) print $i}' |\
# +     sort |\
# +     uniq |\
# +     grep -v '^*' |\
# +     sed -e 's/\.*\*$//'
# +   ))
# +   zstyle ':completion:*:hosts' hosts $_ssh_hosts
# +   unset _ssh_hosts
################################################################################
# put stream annotation here
# stream enable
  _ssh_hosts=($(
    egrep '^Host.*' "$_ssh_configfile" |\
    awk '{for (i=2; i<=NF; i++) print $i}' |\
    sort |\
    uniq |\
    grep -v '^*' |\
    sed -e 's/\.*\*$//'
  ))
  zstyle ':completion:*:hosts' hosts $_ssh_hosts
  unset _ssh_hosts
fi
unset _ssh_configfile

############################################################
# Remove host key from known hosts based on a host section
# name from .ssh/config
function ssh_rmhkey {
  local ssh_configfile="$HOME/.ssh/config"
  local ssh_host="$1"
  if [[ -z "$ssh_host" ]]; then return; fi
  ssh-keygen -R $(grep -A10 "$ssh_host" "$ssh_configfile" | grep -i HostName | head -n 1 | awk '{print $2}')
}
compctl -k hosts ssh_rmhkey

############################################################
# Load SSH key into agent
function ssh_load_key() {
  local key="$1"
  if [[ -z "$key" ]]; then return; fi
  local keyfile="$HOME/.ssh/$key"
  local keysig=$(ssh-keygen -l -f "$keyfile")
  if ( ! ssh-add -l | grep -q "$keysig" ); then
    ssh-add "$keyfile"
  fi
}

############################################################
# Remove SSH key from agent
function ssh_unload_key {
  local key="$1"
  if [[ -z "$key" ]]; then return; fi
  local keyfile="$HOME/.ssh/$key"
  local keysig=$(ssh-keygen -l -f "$keyfile")
  if ( ssh-add -l | grep -q "$keysig" ); then
    ssh-add -d "$keyfile"
  fi
}