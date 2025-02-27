#!/usr/bin/env sh
# Author: non7top@gmail.com
# 07 Jul 2017
# report bugs at https://github.com/non7top/acme.sh

# Values to export:
# export PDD_Token="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

########  Public functions #####################

#Usage: dns_myapi_add   _acme-challenge.www.domain.com   "XKrxpRBosdIKFzxW_CT3KLZNf6q0HG9i01zxXp5CPBs"
dns_yandex_add() {
  fulldomain="${1}"
  txtvalue="${2}"
  _debug "Calling: dns_yandex_add() '${fulldomain}' '${txtvalue}'"
################################################################################
# Commit message: fix egrep and exit
# Commit URL: https://github.com/acmesh-official/acme.sh/commit/10cb7585a7140c7f709e2dcdee27913a55503545
# Category: 
# Notes: 
# Changed content:
# -   _PDD_credentials || exit 1
# +   _PDD_credentials || return 1
################################################################################
# put stream annotation here
# stream enable
  _PDD_credentials || return 1
  export _H1="PddToken: $PDD_Token"

  curDomain="$(echo "${fulldomain}" | rev | cut -d . -f 1-2 | rev)"
  curSubdomain="$(echo "${fulldomain}" | rev | cut -d . -f 3- | rev)"
  curData="domain=${curDomain}&type=TXT&subdomain=${curSubdomain}&ttl=360&content=${txtvalue}"
  curUri="https://pddimp.yandex.ru/api2/admin/dns/add"
  curResult="$(_post "${curData}" "${curUri}")"
  _debug "Result: $curResult"
}

#Usage: dns_myapi_rm   _acme-challenge.www.domain.com
dns_yandex_rm() {
  fulldomain="${1}"
  _debug "Calling: dns_yandex_rm() '${fulldomain}'"
################################################################################
# Commit message: fix egrep and exit
# Commit URL: https://github.com/acmesh-official/acme.sh/commit/10cb7585a7140c7f709e2dcdee27913a55503545
# Category: 
# Notes: 
# Changed content:
# -   _PDD_credentials || exit 1
# +   _PDD_credentials || return 1
################################################################################
# put stream annotation here
# stream enable
  _PDD_credentials || return 1
  export _H1="PddToken: $PDD_Token"
  record_id=$(pdd_get_record_id "${fulldomain}")
  _debug "Result: $record_id"

  curDomain="$(echo "${fulldomain}" | rev | cut -d . -f 1-2 | rev)"
  curSubdomain="$(echo "${fulldomain}" | rev | cut -d . -f 3- | rev)"
  curUri="https://pddimp.yandex.ru/api2/admin/dns/del"
  curData="domain=${curDomain}&record_id=${record_id}"
  curResult="$(_post "${curData}" "${curUri}")"
  _debug "Result: $curResult"
}

####################  Private functions below ##################################

_PDD_credentials() {
  if [ -z "${PDD_Token}" ]; then
    PDD_Token=""
    _err "You haven't specified the ISPConfig Login data."
    return 1
  else
    _saveaccountconf PDD_Token "${PDD_Token}"
  fi
}

pdd_get_record_id() {
  fulldomain="${1}"
  curDomain="$(echo "${fulldomain}" | rev | cut -d . -f 1-2 | rev)"
  curSubdomain="$(echo "${fulldomain}" | rev | cut -d . -f 3- | rev)"
  curUri="https://pddimp.yandex.ru/api2/admin/dns/list?domain=${curDomain}"
  curResult="$(_get "${curUri}" | _normalizeJson)"
  _debug "Result: $curResult"
################################################################################
# Commit message: fix egrep and exit
# Commit URL: https://github.com/acmesh-official/acme.sh/commit/10cb7585a7140c7f709e2dcdee27913a55503545
# Category: 
# Notes: 
# Changed content:
# -   echo "$curResult" | grep -o "{[^{]*\"content\":[^{]*\"subdomain\":\"${curSubdomain}\"" | sed -n -e 's#.* "record_id": \(.*\),[^,]*#\1#p'
# +   echo "$curResult" | _egrep_o "{[^{]*\"content\":[^{]*\"subdomain\":\"${curSubdomain}\"" | sed -n -e 's#.* "record_id": \(.*\),[^,]*#\1#p'
################################################################################
# put stream annotation here
# stream enable
  echo "$curResult" | _egrep_o "{[^{]*\"content\":[^{]*\"subdomain\":\"${curSubdomain}\"" | sed -n -e 's#.* "record_id": \(.*\),[^,]*#\1#p'
}