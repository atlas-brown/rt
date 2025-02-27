#!/usr/bin/env sh

# Supports IONOS DNS API Beta v1.0.0
#
# Usage:
#   Export IONOS_PREFIX and IONOS_SECRET before calling acme.sh:
#
#   $ export IONOS_PREFIX="..."
#   $ export IONOS_SECRET="..."
#
#   $ acme.sh --issue --dns dns_ionos ...

IONOS_API="https://api.hosting.ionos.com/dns"
IONOS_ROUTE_ZONES="/v1/zones"

IONOS_TXT_TTL=60 # minimum accepted by API
IONOS_TXT_PRIO=10

dns_ionos_add() {
  fulldomain=$1
  txtvalue=$2

  if ! _ionos_init; then
    return 1
  fi

  _body="[{\"name\":\"$_sub_domain.$_domain\",\"type\":\"TXT\",\"content\":\"$txtvalue\",\"ttl\":$IONOS_TXT_TTL,\"prio\":$IONOS_TXT_PRIO,\"disabled\":false}]"

  if _ionos_rest POST "$IONOS_ROUTE_ZONES/$_zone_id/records" "$_body" && [ -z "$response" ]; then
    _info "TXT record has been created successfully."
    return 0
  fi

  return 1
}

dns_ionos_rm() {
  fulldomain=$1
  txtvalue=$2

  if ! _ionos_init; then
    return 1
  fi

  if ! _ionos_get_record "$fulldomain" "$_zone_id" "$txtvalue"; then
    _err "Could not find _acme-challenge TXT record."
    return 1
  fi

  if _ionos_rest DELETE "$IONOS_ROUTE_ZONES/$_zone_id/records/$_record_id" && [ -z "$response" ]; then
    _info "TXT record has been deleted successfully."
    return 0
  fi

  return 1
}

_ionos_init() {
  IONOS_PREFIX="${IONOS_PREFIX:-$(_readaccountconf_mutable IONOS_PREFIX)}"
  IONOS_SECRET="${IONOS_SECRET:-$(_readaccountconf_mutable IONOS_SECRET)}"

  if [ -z "$IONOS_PREFIX" ] || [ -z "$IONOS_SECRET" ]; then
    _err "You didn't specify an IONOS api prefix and secret yet."
    _err "Read https://beta.developer.hosting.ionos.de/docs/getstarted to learn how to get a prefix and secret."
    _err ""
    _err "Then set them before calling acme.sh:"
    _err "\$ export IONOS_PREFIX=\"...\""
    _err "\$ export IONOS_SECRET=\"...\""
    _err "\$ acme.sh --issue -d ... --dns dns_ionos"
    return 1
  fi

  _saveaccountconf_mutable IONOS_PREFIX "$IONOS_PREFIX"
  _saveaccountconf_mutable IONOS_SECRET "$IONOS_SECRET"

  if ! _get_root "$fulldomain"; then
    _err "Cannot find this domain in your IONOS account."
    return 1
  fi
}

_get_root() {
  domain=$1
  i=1
  p=1

  if _ionos_rest GET "$IONOS_ROUTE_ZONES"; then
    response="$(echo "$response" | tr -d "\n")"

    while true; do
      h=$(printf "%s" "$domain" | cut -d . -f $i-100)
      if [ -z "$h" ]; then
        return 1
      fi

      _zone="$(echo "$response" | _egrep_o "\"name\":\"$h\".*\}")"
      if [ "$_zone" ]; then
        _zone_id=$(printf "%s\n" "$_zone" | _egrep_o "\"id\":\"[a-fA-F0-9\-]*\"" | _head_n 1 | cut -d : -f 2 | tr -d '\"')
        if [ "$_zone_id" ]; then
          _sub_domain=$(printf "%s" "$domain" | cut -d . -f 1-$p)
          _domain=$h

          return 0
        fi

        return 1
      fi

      p=$i
      i=$(_math "$i" + 1)
    done
  fi

  return 1
}

_ionos_get_record() {
  fulldomain=$1
  zone_id=$2
  txtrecord=$3

  if _ionos_rest GET "$IONOS_ROUTE_ZONES/$zone_id?recordName=$fulldomain&recordType=TXT"; then
    response="$(echo "$response" | tr -d "\n")"

    _record="$(echo "$response" | _egrep_o "\"name\":\"$fulldomain\"[^\}]*\"type\":\"TXT\"[^\}]*\"content\":\"\\\\\"$txtrecord\\\\\"\".*\}")"
    if [ "$_record" ]; then
      _record_id=$(printf "%s\n" "$_record" | _egrep_o "\"id\":\"[a-fA-F0-9\-]*\"" | _head_n 1 | cut -d : -f 2 | tr -d '\"')
################################################################################
# Commit message: Syncing with the original repo (#2)  * change arvan api script  * change Author name  * change name actor  * Updated --preferred-chain to issue ISRG properly  To support different openssl crl2pkcs7 help cli format  * dnsapi/pdns: also normalize json response in detecting root zone  * Chain (#3408)  * fix https://github.com/acmesh-official/acme.sh/issues/3384 match the issuer to the root CA cert subject  * fix format  * fix https://github.com/acmesh-official/acme.sh/issues/3384  * remove the alt files. https://github.com/acmesh-official/acme.sh/issues/3384  * upgrade freebsd and solaris  * duckdns - fix "integer expression expected" errors (#3397)  * fix "integer expression expected" errors  * duckdns fix  * Update dns_duckdns.sh  * Update dns_duckdns.sh  * Implement smtp notify hook  Support notifications via direct SMTP server connection. Uses Python (2.7.x or 3.4+) to communicate with SMTP server.  * Make shfmt happy  (I'm open to better ways of formatting the heredoc that embeds the Python script.)  * Only save config if send is successful  * Add instructions for reporting bugs  * Prep for curl or Python; clean up SMTP_* variable usage  * Implement curl version of smtp notify-hook  * More than one blank line is an abomination, apparently  I will not try to use whitespace to group code visually  * Fix: Unifi deploy hook support Unifi Cloud Key (#3327)  * fix: unifi deploy hook also update Cloud Key nginx certs  When running on a Unifi Cloud Key device, also deploy to /etc/ssl/private/cloudkey.{crt,key} and reload nginx. This makes the new cert available for the Cloud Key management app running via nginx on port 443 (as well as the port 8443 Unifi Controller app the deploy hook already supported).  Fixes #3326  * Improve settings documentation comments  * Improve Cloud Key pre-flight error messaging  * Fix typo  * Add support for UnifiOS (Cloud Key Gen2)  Since UnifiOS does not use the Java keystore (like a Unifi Controller or Cloud Key Gen1 deploy), this also reworks the settings validation and error messaging somewhat.  * PR review fixes  * Detect unsupported Cloud Key java keystore location  * Don't try to restart inactive services  (and remove extra spaces from reload command)  * Clean up error messages and internal variables  * Change to _getdeployconf/_savedeployconf  * Switch from cp to cat to preserve file permissions  * feat: add huaweicloud error handling  * fix: fix freebsd and solaris  * support openssl 3.0 fix https://github.com/acmesh-official/acme.sh/issues/3399  * make the fix for rsa key only  * Use PROJECT_NAME and VER for X-Mailer header  Also add X-Mailer header to Python version  * Add _clearaccountconf_mutable()  * Rework read/save config to not save default values  Add and use _readaccountconf_mutable_default and _saveaccountconf_mutable_default helpers to capture common default value handling.  New approach also eliminates need for separate underscore-prefixed version of each conf var.  * Implement _rfc2822_date helper  * Clean email headers and warn on unsupported address format  Just in case, make sure CR or NL don't end up in an email header.  * Clarify _readaccountconf_mutable_default  * Add Date email header in Python implementation  * Use email.policy.default in Python 3 implementation  Improves standards compatibility and utf-8 handling in Python 3.3-3.8. (email.policy.default becomes the default in Python 3.9.)  * Prefer Python to curl when both available  * Change default SMTP_SECURE to "tls"  Secure by default. Also try to minimize configuration errors. (Many ESPs/ISPs require STARTTLS, and most support it.)  * Update dns_dp.sh  没有encode中文字符会导致提交失败  * No need to include EC parameters explicitly with the private key. (they are embedded)  * Fixes response handling and thereby allow issuing of subdomain certs  * Adds comment  * fix https://github.com/acmesh-official/acme.sh/issues/3402  * dnsapi/ionos: Use POST instead of PATCH for adding TXT record  The API now supports a POST route for adding records. Therefore checking for already existing records and including them in a PATCH request is no longer necessary.  * fix https://github.com/acmesh-official/acme.sh/issues/3433  * fix https://github.com/acmesh-official/acme.sh/issues/3019  * fix format  * Update dns_servercow.sh to support wildcard certs  Updated dns_servercow.sh to support txt records with multiple entries. This supports wildcard certificates that require txt records with the same name and different contents.  * Update dns_servercow.sh to support wildcard certs  Updated dns_servercow.sh to support txt records with multiple entries. This supports wildcard certificates that require txt records with the same name and different contents.  * fix https://github.com/acmesh-official/acme.sh/issues/3312  * fix format  * feat: add dns_porkbun  * fix: prevent rate limit  Co-authored-by: Vahid Fardi <vahid.fardi@snapp.cab> Co-authored-by: neil <github@neilpang.com> Co-authored-by: Gnought <1684105+gnought@users.noreply.github.com> Co-authored-by: manuel <manuel@mausz.at> Co-authored-by: jerrm <jerrm@users.noreply.github.com> Co-authored-by: medmunds <medmunds@gmail.com> Co-authored-by: Mike Edmunds <github@to.mikeedmunds.com> Co-authored-by: Easton Man <manyang.me@outlook.com> Co-authored-by: czeming <loser_wind@163.com> Co-authored-by: Geert Hendrickx <geert@hendrickx.be> Co-authored-by: Kristian Johansson <kristian.johansson86@gmail.com> Co-authored-by: Lukas Brocke <lukas@brocke.net> Co-authored-by: anom-human <80478363+anom-human@users.noreply.github.com> Co-authored-by: neil <win10@neilpang.com> Co-authored-by: Quentin Dreyer <quentin.dreyer@rgsystem.com>
# Commit URL: https://github.com/acmesh-official/acme.sh/commit/c384ed960c138f4449e79293644c4d0ec937cef1
# Category: 
# Notes: 
# Changed content:
# - _ionos_get_existing_records() {
# -   fulldomain=$1
# -   zone_id=$2
# - 
# -   if _ionos_rest GET "$IONOS_ROUTE_ZONES/$zone_id?recordName=$fulldomain&recordType=TXT"; then
# -     response="$(echo "$response" | tr -d "\n")"
# - 
# -     _existing_records="$(printf "%s\n" "$response" | _egrep_o "\"records\":\[.*\]" | _head_n 1 | cut -d '[' -f 2 | sed 's/]//')"
# -   fi
# - }
# - 
################################################################################
# put stream annotation here
# stream enable

      return 0
    fi
  fi

  return 1
}

_ionos_rest() {
  method="$1"
  route="$2"
  data="$3"

  IONOS_API_KEY="$(printf "%s.%s" "$IONOS_PREFIX" "$IONOS_SECRET")"

  export _H1="X-API-Key: $IONOS_API_KEY"

  if [ "$method" != "GET" ]; then
    export _H2="Accept: application/json"
    export _H3="Content-Type: application/json"

    response="$(_post "$data" "$IONOS_API$route" "" "$method" "application/json")"
  else
    export _H2="Accept: */*"

    response="$(_get "$IONOS_API$route")"
  fi

  if [ "$?" != "0" ]; then
    _err "Error $route"
    return 1
  fi

  return 0
}