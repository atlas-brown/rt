#!/usr/bin/env sh

#PowerDNS Embedded API
#https://doc.powerdns.com/md/httpapi/api_spec/
#
#PDNS_Url="http://ns.example.com:8081"
#PDNS_ServerId="localhost"
#PDNS_Token="0123456789ABCDEF"
#PDNS_Ttl=60

DEFAULT_PDNS_TTL=60

########  Public functions #####################
#Usage: add _acme-challenge.www.domain.com "123456789ABCDEF0000000000000000000000000000000000000"
#fulldomain
#txtvalue
dns_pdns_add() {
  fulldomain=$1
  txtvalue=$2

  if [ -z "$PDNS_Url" ]; then
    PDNS_Url=""
    _err "You don't specify PowerDNS address."
    _err "Please set PDNS_Url and try again."
    return 1
  fi

  if [ -z "$PDNS_ServerId" ]; then
    PDNS_ServerId=""
    _err "You don't specify PowerDNS server id."
    _err "Please set you PDNS_ServerId and try again."
    return 1
  fi

  if [ -z "$PDNS_Token" ]; then
    PDNS_Token=""
    _err "You don't specify PowerDNS token."
    _err "Please create you PDNS_Token and try again."
    return 1
  fi

  if [ -z "$PDNS_Ttl" ]; then
    PDNS_Ttl="$DEFAULT_PDNS_TTL"
  fi

  #save the api addr and key to the account conf file.
  _saveaccountconf PDNS_Url "$PDNS_Url"
  _saveaccountconf PDNS_ServerId "$PDNS_ServerId"
  _saveaccountconf PDNS_Token "$PDNS_Token"

  if [ "$PDNS_Ttl" != "$DEFAULT_PDNS_TTL" ]; then
    _saveaccountconf PDNS_Ttl "$PDNS_Ttl"
  fi

  _debug "Detect root zone"
  if ! _get_root "$fulldomain"; then
    _err "invalid domain"
    return 1
  fi
  _debug _domain "$_domain"

  if ! set_record "$_domain" "$fulldomain" "$txtvalue"; then
    return 1
  fi

  return 0
}

#fulldomain
dns_pdns_rm() {
  fulldomain=$1
  txtvalue=$2

  if [ -z "$PDNS_Ttl" ]; then
    PDNS_Ttl="$DEFAULT_PDNS_TTL"
  fi

  _debug "Detect root zone"
  if ! _get_root "$fulldomain"; then
    _err "invalid domain"
    return 1
  fi

  _debug _domain "$_domain"

  if ! rm_record "$_domain" "$fulldomain" "$txtvalue"; then
    return 1
  fi

  return 0
}

set_record() {
  _info "Adding record"
  root=$1
  full=$2
  new_challenge=$3

  _record_string=""
  _build_record_string "$new_challenge"
  _list_existingchallenges
  for oldchallenge in $_existing_challenges; do
    _build_record_string "$oldchallenge"
  done

  if ! _pdns_rest "PATCH" "/api/v1/servers/$PDNS_ServerId/zones/$root" "{\"rrsets\": [{\"changetype\": \"REPLACE\", \"name\": \"$full.\", \"type\": \"TXT\", \"ttl\": $PDNS_Ttl, \"records\": [$_record_string]}]}"; then
    _err "Set txt record error."
    return 1
  fi

  if ! notify_slaves "$root"; then
    return 1
  fi

  return 0
}

rm_record() {
  _info "Remove record"
  root=$1
  full=$2
  txtvalue=$3

  #Enumerate existing acme challenges
  _list_existingchallenges

  if _contains "$_existing_challenges" "$txtvalue"; then
    #Delete all challenges (PowerDNS API does not allow to delete content)
    if ! _pdns_rest "PATCH" "/api/v1/servers/$PDNS_ServerId/zones/$root" "{\"rrsets\": [{\"changetype\": \"DELETE\", \"name\": \"$full.\", \"type\": \"TXT\"}]}"; then
      _err "Delete txt record error."
      return 1
    fi
    _record_string=""
    #If the only existing challenge was the challenge to delete: nothing to do
    if ! [ "$_existing_challenges" = "$txtvalue" ]; then
      for oldchallenge in $_existing_challenges; do
        #Build up the challenges to re-add, ommitting the one what should be deleted
        if ! [ "$oldchallenge" = "$txtvalue" ]; then
          _build_record_string "$oldchallenge"
        fi
      done
      #Recreate the existing challenges
      if ! _pdns_rest "PATCH" "/api/v1/servers/$PDNS_ServerId/zones/$root" "{\"rrsets\": [{\"changetype\": \"REPLACE\", \"name\": \"$full.\", \"type\": \"TXT\", \"ttl\": $PDNS_Ttl, \"records\": [$_record_string]}]}"; then
        _err "Set txt record error."
        return 1
      fi
    fi
    if ! notify_slaves "$root"; then
      return 1
    fi
  else
    _info "Record not found, nothing to remove"
  fi

  return 0
}

notify_slaves() {
  root=$1

  if ! _pdns_rest "PUT" "/api/v1/servers/$PDNS_ServerId/zones/$root/notify"; then
    _err "Notify slaves error."
    return 1
  fi

  return 0
}

####################  Private functions below ##################################
#_acme-challenge.www.domain.com
#returns
# _domain=domain.com
_get_root() {
  domain=$1
  i=1

  if _pdns_rest "GET" "/api/v1/servers/$PDNS_ServerId/zones"; then
################################################################################
# Commit message: Syncing with the original repo (#2)  * change arvan api script  * change Author name  * change name actor  * Updated --preferred-chain to issue ISRG properly  To support different openssl crl2pkcs7 help cli format  * dnsapi/pdns: also normalize json response in detecting root zone  * Chain (#3408)  * fix https://github.com/acmesh-official/acme.sh/issues/3384 match the issuer to the root CA cert subject  * fix format  * fix https://github.com/acmesh-official/acme.sh/issues/3384  * remove the alt files. https://github.com/acmesh-official/acme.sh/issues/3384  * upgrade freebsd and solaris  * duckdns - fix "integer expression expected" errors (#3397)  * fix "integer expression expected" errors  * duckdns fix  * Update dns_duckdns.sh  * Update dns_duckdns.sh  * Implement smtp notify hook  Support notifications via direct SMTP server connection. Uses Python (2.7.x or 3.4+) to communicate with SMTP server.  * Make shfmt happy  (I'm open to better ways of formatting the heredoc that embeds the Python script.)  * Only save config if send is successful  * Add instructions for reporting bugs  * Prep for curl or Python; clean up SMTP_* variable usage  * Implement curl version of smtp notify-hook  * More than one blank line is an abomination, apparently  I will not try to use whitespace to group code visually  * Fix: Unifi deploy hook support Unifi Cloud Key (#3327)  * fix: unifi deploy hook also update Cloud Key nginx certs  When running on a Unifi Cloud Key device, also deploy to /etc/ssl/private/cloudkey.{crt,key} and reload nginx. This makes the new cert available for the Cloud Key management app running via nginx on port 443 (as well as the port 8443 Unifi Controller app the deploy hook already supported).  Fixes #3326  * Improve settings documentation comments  * Improve Cloud Key pre-flight error messaging  * Fix typo  * Add support for UnifiOS (Cloud Key Gen2)  Since UnifiOS does not use the Java keystore (like a Unifi Controller or Cloud Key Gen1 deploy), this also reworks the settings validation and error messaging somewhat.  * PR review fixes  * Detect unsupported Cloud Key java keystore location  * Don't try to restart inactive services  (and remove extra spaces from reload command)  * Clean up error messages and internal variables  * Change to _getdeployconf/_savedeployconf  * Switch from cp to cat to preserve file permissions  * feat: add huaweicloud error handling  * fix: fix freebsd and solaris  * support openssl 3.0 fix https://github.com/acmesh-official/acme.sh/issues/3399  * make the fix for rsa key only  * Use PROJECT_NAME and VER for X-Mailer header  Also add X-Mailer header to Python version  * Add _clearaccountconf_mutable()  * Rework read/save config to not save default values  Add and use _readaccountconf_mutable_default and _saveaccountconf_mutable_default helpers to capture common default value handling.  New approach also eliminates need for separate underscore-prefixed version of each conf var.  * Implement _rfc2822_date helper  * Clean email headers and warn on unsupported address format  Just in case, make sure CR or NL don't end up in an email header.  * Clarify _readaccountconf_mutable_default  * Add Date email header in Python implementation  * Use email.policy.default in Python 3 implementation  Improves standards compatibility and utf-8 handling in Python 3.3-3.8. (email.policy.default becomes the default in Python 3.9.)  * Prefer Python to curl when both available  * Change default SMTP_SECURE to "tls"  Secure by default. Also try to minimize configuration errors. (Many ESPs/ISPs require STARTTLS, and most support it.)  * Update dns_dp.sh  没有encode中文字符会导致提交失败  * No need to include EC parameters explicitly with the private key. (they are embedded)  * Fixes response handling and thereby allow issuing of subdomain certs  * Adds comment  * fix https://github.com/acmesh-official/acme.sh/issues/3402  * dnsapi/ionos: Use POST instead of PATCH for adding TXT record  The API now supports a POST route for adding records. Therefore checking for already existing records and including them in a PATCH request is no longer necessary.  * fix https://github.com/acmesh-official/acme.sh/issues/3433  * fix https://github.com/acmesh-official/acme.sh/issues/3019  * fix format  * Update dns_servercow.sh to support wildcard certs  Updated dns_servercow.sh to support txt records with multiple entries. This supports wildcard certificates that require txt records with the same name and different contents.  * Update dns_servercow.sh to support wildcard certs  Updated dns_servercow.sh to support txt records with multiple entries. This supports wildcard certificates that require txt records with the same name and different contents.  * fix https://github.com/acmesh-official/acme.sh/issues/3312  * fix format  * feat: add dns_porkbun  * fix: prevent rate limit  Co-authored-by: Vahid Fardi <vahid.fardi@snapp.cab> Co-authored-by: neil <github@neilpang.com> Co-authored-by: Gnought <1684105+gnought@users.noreply.github.com> Co-authored-by: manuel <manuel@mausz.at> Co-authored-by: jerrm <jerrm@users.noreply.github.com> Co-authored-by: medmunds <medmunds@gmail.com> Co-authored-by: Mike Edmunds <github@to.mikeedmunds.com> Co-authored-by: Easton Man <manyang.me@outlook.com> Co-authored-by: czeming <loser_wind@163.com> Co-authored-by: Geert Hendrickx <geert@hendrickx.be> Co-authored-by: Kristian Johansson <kristian.johansson86@gmail.com> Co-authored-by: Lukas Brocke <lukas@brocke.net> Co-authored-by: anom-human <80478363+anom-human@users.noreply.github.com> Co-authored-by: neil <win10@neilpang.com> Co-authored-by: Quentin Dreyer <quentin.dreyer@rgsystem.com>
# Commit URL: https://github.com/acmesh-official/acme.sh/commit/c384ed960c138f4449e79293644c4d0ec937cef1
# Category: 
# Notes: 
# Changed content:
# -     _zones_response="$response"
# +     _zones_response=$(echo "$response" | _normalizeJson)
################################################################################
# put stream annotation here
# stream enable
    _zones_response="$response"
  fi

  while true; do
    h=$(printf "%s" "$domain" | cut -d . -f $i-100)

    if _contains "$_zones_response" "\"name\": \"$h.\""; then
      _domain="$h."
      if [ -z "$h" ]; then
        _domain="=2E"
      fi
      return 0
    fi

    if [ -z "$h" ]; then
      return 1
    fi
    i=$(_math $i + 1)
  done
  _debug "$domain not found"

  return 1
}

_pdns_rest() {
  method=$1
  ep=$2
  data=$3

  export _H1="X-API-Key: $PDNS_Token"

  if [ ! "$method" = "GET" ]; then
    _debug data "$data"
    response="$(_post "$data" "$PDNS_Url$ep" "" "$method")"
  else
    response="$(_get "$PDNS_Url$ep")"
  fi

  if [ "$?" != "0" ]; then
    _err "error $ep"
    return 1
  fi
  _debug2 response "$response"

  return 0
}

_build_record_string() {
  _record_string="${_record_string:+${_record_string}, }{\"content\": \"\\\"${1}\\\"\", \"disabled\": false}"
}

_list_existingchallenges() {
  _pdns_rest "GET" "/api/v1/servers/$PDNS_ServerId/zones/$root"
  _existing_challenges=$(echo "$response" | _normalizeJson | _egrep_o "\"name\":\"${fulldomain}[^]]*}" | _egrep_o 'content\":\"\\"[^\\]*' | sed -n 's/^content":"\\"//p')
}