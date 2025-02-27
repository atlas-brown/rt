#!/usr/bin/env sh

##########
# Custom servercow.de DNS API v1 for use with [acme.sh](https://github.com/acmesh-official/acme.sh)
#
# Usage:
# export SERVERCOW_API_Username=username
# export SERVERCOW_API_Password=password
# acme.sh --issue -d example.com --dns dns_servercow
#
# Issues:
# Any issues / questions / suggestions can be posted here:
# https://github.com/jhartlep/servercow-dns-api/issues
#
# Author: Jens Hartlep
##########

SERVERCOW_API="https://api.servercow.de/dns/v1/domains"

# Usage dns_servercow_add _acme-challenge.www.domain.com "abcdefghijklmnopqrstuvwxyz"
dns_servercow_add() {
  fulldomain=$1
  txtvalue=$2

  _info "Using servercow"
  _debug fulldomain "$fulldomain"
  _debug txtvalue "$txtvalue"

  SERVERCOW_API_Username="${SERVERCOW_API_Username:-$(_readaccountconf_mutable SERVERCOW_API_Username)}"
  SERVERCOW_API_Password="${SERVERCOW_API_Password:-$(_readaccountconf_mutable SERVERCOW_API_Password)}"
  if [ -z "$SERVERCOW_API_Username" ] || [ -z "$SERVERCOW_API_Password" ]; then
    SERVERCOW_API_Username=""
    SERVERCOW_API_Password=""
    _err "You don't specify servercow api username and password yet."
    _err "Please create your username and password and try again."
    return 1
  fi

  # save the credentials to the account conf file
  _saveaccountconf_mutable SERVERCOW_API_Username "$SERVERCOW_API_Username"
  _saveaccountconf_mutable SERVERCOW_API_Password "$SERVERCOW_API_Password"

  _debug "First detect the root zone"
  if ! _get_root "$fulldomain"; then
    _err "invalid domain"
    return 1
  fi

  _debug _sub_domain "$_sub_domain"
  _debug _domain "$_domain"

################################################################################
# Commit message: Syncing with the original repo (#2)  * change arvan api script  * change Author name  * change name actor  * Updated --preferred-chain to issue ISRG properly  To support different openssl crl2pkcs7 help cli format  * dnsapi/pdns: also normalize json response in detecting root zone  * Chain (#3408)  * fix https://github.com/acmesh-official/acme.sh/issues/3384 match the issuer to the root CA cert subject  * fix format  * fix https://github.com/acmesh-official/acme.sh/issues/3384  * remove the alt files. https://github.com/acmesh-official/acme.sh/issues/3384  * upgrade freebsd and solaris  * duckdns - fix "integer expression expected" errors (#3397)  * fix "integer expression expected" errors  * duckdns fix  * Update dns_duckdns.sh  * Update dns_duckdns.sh  * Implement smtp notify hook  Support notifications via direct SMTP server connection. Uses Python (2.7.x or 3.4+) to communicate with SMTP server.  * Make shfmt happy  (I'm open to better ways of formatting the heredoc that embeds the Python script.)  * Only save config if send is successful  * Add instructions for reporting bugs  * Prep for curl or Python; clean up SMTP_* variable usage  * Implement curl version of smtp notify-hook  * More than one blank line is an abomination, apparently  I will not try to use whitespace to group code visually  * Fix: Unifi deploy hook support Unifi Cloud Key (#3327)  * fix: unifi deploy hook also update Cloud Key nginx certs  When running on a Unifi Cloud Key device, also deploy to /etc/ssl/private/cloudkey.{crt,key} and reload nginx. This makes the new cert available for the Cloud Key management app running via nginx on port 443 (as well as the port 8443 Unifi Controller app the deploy hook already supported).  Fixes #3326  * Improve settings documentation comments  * Improve Cloud Key pre-flight error messaging  * Fix typo  * Add support for UnifiOS (Cloud Key Gen2)  Since UnifiOS does not use the Java keystore (like a Unifi Controller or Cloud Key Gen1 deploy), this also reworks the settings validation and error messaging somewhat.  * PR review fixes  * Detect unsupported Cloud Key java keystore location  * Don't try to restart inactive services  (and remove extra spaces from reload command)  * Clean up error messages and internal variables  * Change to _getdeployconf/_savedeployconf  * Switch from cp to cat to preserve file permissions  * feat: add huaweicloud error handling  * fix: fix freebsd and solaris  * support openssl 3.0 fix https://github.com/acmesh-official/acme.sh/issues/3399  * make the fix for rsa key only  * Use PROJECT_NAME and VER for X-Mailer header  Also add X-Mailer header to Python version  * Add _clearaccountconf_mutable()  * Rework read/save config to not save default values  Add and use _readaccountconf_mutable_default and _saveaccountconf_mutable_default helpers to capture common default value handling.  New approach also eliminates need for separate underscore-prefixed version of each conf var.  * Implement _rfc2822_date helper  * Clean email headers and warn on unsupported address format  Just in case, make sure CR or NL don't end up in an email header.  * Clarify _readaccountconf_mutable_default  * Add Date email header in Python implementation  * Use email.policy.default in Python 3 implementation  Improves standards compatibility and utf-8 handling in Python 3.3-3.8. (email.policy.default becomes the default in Python 3.9.)  * Prefer Python to curl when both available  * Change default SMTP_SECURE to "tls"  Secure by default. Also try to minimize configuration errors. (Many ESPs/ISPs require STARTTLS, and most support it.)  * Update dns_dp.sh  没有encode中文字符会导致提交失败  * No need to include EC parameters explicitly with the private key. (they are embedded)  * Fixes response handling and thereby allow issuing of subdomain certs  * Adds comment  * fix https://github.com/acmesh-official/acme.sh/issues/3402  * dnsapi/ionos: Use POST instead of PATCH for adding TXT record  The API now supports a POST route for adding records. Therefore checking for already existing records and including them in a PATCH request is no longer necessary.  * fix https://github.com/acmesh-official/acme.sh/issues/3433  * fix https://github.com/acmesh-official/acme.sh/issues/3019  * fix format  * Update dns_servercow.sh to support wildcard certs  Updated dns_servercow.sh to support txt records with multiple entries. This supports wildcard certificates that require txt records with the same name and different contents.  * Update dns_servercow.sh to support wildcard certs  Updated dns_servercow.sh to support txt records with multiple entries. This supports wildcard certificates that require txt records with the same name and different contents.  * fix https://github.com/acmesh-official/acme.sh/issues/3312  * fix format  * feat: add dns_porkbun  * fix: prevent rate limit  Co-authored-by: Vahid Fardi <vahid.fardi@snapp.cab> Co-authored-by: neil <github@neilpang.com> Co-authored-by: Gnought <1684105+gnought@users.noreply.github.com> Co-authored-by: manuel <manuel@mausz.at> Co-authored-by: jerrm <jerrm@users.noreply.github.com> Co-authored-by: medmunds <medmunds@gmail.com> Co-authored-by: Mike Edmunds <github@to.mikeedmunds.com> Co-authored-by: Easton Man <manyang.me@outlook.com> Co-authored-by: czeming <loser_wind@163.com> Co-authored-by: Geert Hendrickx <geert@hendrickx.be> Co-authored-by: Kristian Johansson <kristian.johansson86@gmail.com> Co-authored-by: Lukas Brocke <lukas@brocke.net> Co-authored-by: anom-human <80478363+anom-human@users.noreply.github.com> Co-authored-by: neil <win10@neilpang.com> Co-authored-by: Quentin Dreyer <quentin.dreyer@rgsystem.com>
# Commit URL: https://github.com/acmesh-official/acme.sh/commit/c384ed960c138f4449e79293644c4d0ec937cef1
# Category: 
# Notes: 
# Changed content:
# -   if _servercow_api POST "$_domain" "{\"type\":\"TXT\",\"name\":\"$fulldomain\",\"content\":\"$txtvalue\",\"ttl\":20}"; then
# -     if printf -- "%s" "$response" | grep "ok" >/dev/null; then
# -       _info "Added, OK"
# -       return 0
# -     else
# -       _err "add txt record error."
# -       return 1
# +   # check whether a txt record already exists for the subdomain
# +   if printf -- "%s" "$response" | grep "{\"name\":\"$_sub_domain\",\"ttl\":20,\"type\":\"TXT\"" >/dev/null; then
# +     _info "A txt record with the same name already exists."
# +     # trim the string on the left
# +     txtvalue_old=${response#*{\"name\":\"$_sub_domain\",\"ttl\":20,\"type\":\"TXT\",\"content\":\"}
# +     # trim the string on the right
# +     txtvalue_old=${txtvalue_old%%\"*}
# + 
# +     _debug txtvalue_old "$txtvalue_old"
# + 
# +     _info "Add the new txtvalue to the existing txt record."
# +     if _servercow_api POST "$_domain" "{\"type\":\"TXT\",\"name\":\"$fulldomain\",\"content\":[\"$txtvalue\",\"$txtvalue_old\"],\"ttl\":20}"; then
# +       if printf -- "%s" "$response" | grep "ok" >/dev/null; then
# +         _info "Added additional txtvalue, OK"
# +         return 0
# +       else
# +         _err "add txt record error."
# +         return 1
# +       fi
################################################################################
# put stream annotation here
# stream enable
  # check whether a txt record already exists for the subdomain
  if printf -- "%s" "$response" | grep "{\"name\":\"$_sub_domain\",\"ttl\":20,\"type\":\"TXT\"" >/dev/null; then
    _info "A txt record with the same name already exists."
    # trim the string on the left
    txtvalue_old=${response#*{\"name\":\"$_sub_domain\",\"ttl\":20,\"type\":\"TXT\",\"content\":\"}
    # trim the string on the right
    txtvalue_old=${txtvalue_old%%\"*}

    _debug txtvalue_old "$txtvalue_old"

    _info "Add the new txtvalue to the existing txt record."
    if _servercow_api POST "$_domain" "{\"type\":\"TXT\",\"name\":\"$fulldomain\",\"content\":[\"$txtvalue\",\"$txtvalue_old\"],\"ttl\":20}"; then
      if printf -- "%s" "$response" | grep "ok" >/dev/null; then
        _info "Added additional txtvalue, OK"
        return 0
      else
        _err "add txt record error."
        return 1
      fi
    fi
################################################################################
# Commit message: Syncing with the original repo (#2)  * change arvan api script  * change Author name  * change name actor  * Updated --preferred-chain to issue ISRG properly  To support different openssl crl2pkcs7 help cli format  * dnsapi/pdns: also normalize json response in detecting root zone  * Chain (#3408)  * fix https://github.com/acmesh-official/acme.sh/issues/3384 match the issuer to the root CA cert subject  * fix format  * fix https://github.com/acmesh-official/acme.sh/issues/3384  * remove the alt files. https://github.com/acmesh-official/acme.sh/issues/3384  * upgrade freebsd and solaris  * duckdns - fix "integer expression expected" errors (#3397)  * fix "integer expression expected" errors  * duckdns fix  * Update dns_duckdns.sh  * Update dns_duckdns.sh  * Implement smtp notify hook  Support notifications via direct SMTP server connection. Uses Python (2.7.x or 3.4+) to communicate with SMTP server.  * Make shfmt happy  (I'm open to better ways of formatting the heredoc that embeds the Python script.)  * Only save config if send is successful  * Add instructions for reporting bugs  * Prep for curl or Python; clean up SMTP_* variable usage  * Implement curl version of smtp notify-hook  * More than one blank line is an abomination, apparently  I will not try to use whitespace to group code visually  * Fix: Unifi deploy hook support Unifi Cloud Key (#3327)  * fix: unifi deploy hook also update Cloud Key nginx certs  When running on a Unifi Cloud Key device, also deploy to /etc/ssl/private/cloudkey.{crt,key} and reload nginx. This makes the new cert available for the Cloud Key management app running via nginx on port 443 (as well as the port 8443 Unifi Controller app the deploy hook already supported).  Fixes #3326  * Improve settings documentation comments  * Improve Cloud Key pre-flight error messaging  * Fix typo  * Add support for UnifiOS (Cloud Key Gen2)  Since UnifiOS does not use the Java keystore (like a Unifi Controller or Cloud Key Gen1 deploy), this also reworks the settings validation and error messaging somewhat.  * PR review fixes  * Detect unsupported Cloud Key java keystore location  * Don't try to restart inactive services  (and remove extra spaces from reload command)  * Clean up error messages and internal variables  * Change to _getdeployconf/_savedeployconf  * Switch from cp to cat to preserve file permissions  * feat: add huaweicloud error handling  * fix: fix freebsd and solaris  * support openssl 3.0 fix https://github.com/acmesh-official/acme.sh/issues/3399  * make the fix for rsa key only  * Use PROJECT_NAME and VER for X-Mailer header  Also add X-Mailer header to Python version  * Add _clearaccountconf_mutable()  * Rework read/save config to not save default values  Add and use _readaccountconf_mutable_default and _saveaccountconf_mutable_default helpers to capture common default value handling.  New approach also eliminates need for separate underscore-prefixed version of each conf var.  * Implement _rfc2822_date helper  * Clean email headers and warn on unsupported address format  Just in case, make sure CR or NL don't end up in an email header.  * Clarify _readaccountconf_mutable_default  * Add Date email header in Python implementation  * Use email.policy.default in Python 3 implementation  Improves standards compatibility and utf-8 handling in Python 3.3-3.8. (email.policy.default becomes the default in Python 3.9.)  * Prefer Python to curl when both available  * Change default SMTP_SECURE to "tls"  Secure by default. Also try to minimize configuration errors. (Many ESPs/ISPs require STARTTLS, and most support it.)  * Update dns_dp.sh  没有encode中文字符会导致提交失败  * No need to include EC parameters explicitly with the private key. (they are embedded)  * Fixes response handling and thereby allow issuing of subdomain certs  * Adds comment  * fix https://github.com/acmesh-official/acme.sh/issues/3402  * dnsapi/ionos: Use POST instead of PATCH for adding TXT record  The API now supports a POST route for adding records. Therefore checking for already existing records and including them in a PATCH request is no longer necessary.  * fix https://github.com/acmesh-official/acme.sh/issues/3433  * fix https://github.com/acmesh-official/acme.sh/issues/3019  * fix format  * Update dns_servercow.sh to support wildcard certs  Updated dns_servercow.sh to support txt records with multiple entries. This supports wildcard certificates that require txt records with the same name and different contents.  * Update dns_servercow.sh to support wildcard certs  Updated dns_servercow.sh to support txt records with multiple entries. This supports wildcard certificates that require txt records with the same name and different contents.  * fix https://github.com/acmesh-official/acme.sh/issues/3312  * fix format  * feat: add dns_porkbun  * fix: prevent rate limit  Co-authored-by: Vahid Fardi <vahid.fardi@snapp.cab> Co-authored-by: neil <github@neilpang.com> Co-authored-by: Gnought <1684105+gnought@users.noreply.github.com> Co-authored-by: manuel <manuel@mausz.at> Co-authored-by: jerrm <jerrm@users.noreply.github.com> Co-authored-by: medmunds <medmunds@gmail.com> Co-authored-by: Mike Edmunds <github@to.mikeedmunds.com> Co-authored-by: Easton Man <manyang.me@outlook.com> Co-authored-by: czeming <loser_wind@163.com> Co-authored-by: Geert Hendrickx <geert@hendrickx.be> Co-authored-by: Kristian Johansson <kristian.johansson86@gmail.com> Co-authored-by: Lukas Brocke <lukas@brocke.net> Co-authored-by: anom-human <80478363+anom-human@users.noreply.github.com> Co-authored-by: neil <win10@neilpang.com> Co-authored-by: Quentin Dreyer <quentin.dreyer@rgsystem.com>
# Commit URL: https://github.com/acmesh-official/acme.sh/commit/c384ed960c138f4449e79293644c4d0ec937cef1
# Category: 
# Notes: 
# Changed content:
# +     _err "add txt record error."
# +     return 1
# +   else
# +     _info "There is no txt record with the name yet."
# +     if _servercow_api POST "$_domain" "{\"type\":\"TXT\",\"name\":\"$fulldomain\",\"content\":\"$txtvalue\",\"ttl\":20}"; then
# +       if printf -- "%s" "$response" | grep "ok" >/dev/null; then
# +         _info "Added, OK"
# +         return 0
# +       else
# +         _err "add txt record error."
# +         return 1
# +       fi
# +     fi
# +     _err "add txt record error."
# +     return 1
################################################################################
# put stream annotation here
# stream enable
    _err "add txt record error."
    return 1
  else
    _info "There is no txt record with the name yet."
    if _servercow_api POST "$_domain" "{\"type\":\"TXT\",\"name\":\"$fulldomain\",\"content\":\"$txtvalue\",\"ttl\":20}"; then
      if printf -- "%s" "$response" | grep "ok" >/dev/null; then
        _info "Added, OK"
        return 0
      else
        _err "add txt record error."
        return 1
      fi
    fi
    _err "add txt record error."
    return 1
  fi

  return 1
}

# Usage fulldomain txtvalue
# Remove the txt record after validation
dns_servercow_rm() {
  fulldomain=$1
  txtvalue=$2

  _info "Using servercow"
  _debug fulldomain "$fulldomain"
  _debug txtvalue "$fulldomain"

  SERVERCOW_API_Username="${SERVERCOW_API_Username:-$(_readaccountconf_mutable SERVERCOW_API_Username)}"
  SERVERCOW_API_Password="${SERVERCOW_API_Password:-$(_readaccountconf_mutable SERVERCOW_API_Password)}"
  if [ -z "$SERVERCOW_API_Username" ] || [ -z "$SERVERCOW_API_Password" ]; then
    SERVERCOW_API_Username=""
    SERVERCOW_API_Password=""
    _err "You don't specify servercow api username and password yet."
    _err "Please create your username and password and try again."
    return 1
  fi

  _debug "First detect the root zone"
  if ! _get_root "$fulldomain"; then
    _err "invalid domain"
    return 1
  fi

  _debug _sub_domain "$_sub_domain"
  _debug _domain "$_domain"

  if _servercow_api DELETE "$_domain" "{\"type\":\"TXT\",\"name\":\"$fulldomain\"}"; then
    if printf -- "%s" "$response" | grep "ok" >/dev/null; then
      _info "Deleted, OK"
      _contains "$response" '"message":"ok"'
    else
      _err "delete txt record error."
      return 1
    fi
  fi

}

####################  Private functions below ##################################

# _acme-challenge.www.domain.com
# returns
#  _sub_domain=_acme-challenge.www
#  _domain=domain.com
_get_root() {
  fulldomain=$1
  i=2
  p=1

  while true; do
    _domain=$(printf "%s" "$fulldomain" | cut -d . -f $i-100)

    _debug _domain "$_domain"
    if [ -z "$_domain" ]; then
      # not valid
      return 1
    fi

    if ! _servercow_api GET "$_domain"; then
      return 1
    fi

    if ! _contains "$response" '"error":"no such domain in user context"' >/dev/null; then
      _sub_domain=$(printf "%s" "$fulldomain" | cut -d . -f 1-$p)
      if [ -z "$_sub_domain" ]; then
        # not valid
        return 1
      fi

      return 0
    fi

    p=$i
    i=$(_math "$i" + 1)
  done

  return 1
}

_servercow_api() {
  method=$1
  domain=$2
  data="$3"

  export _H1="Content-Type: application/json"
  export _H2="X-Auth-Username: $SERVERCOW_API_Username"
  export _H3="X-Auth-Password: $SERVERCOW_API_Password"

  if [ "$method" != "GET" ]; then
    _debug data "$data"
    response="$(_post "$data" "$SERVERCOW_API/$domain" "" "$method")"
  else
    response="$(_get "$SERVERCOW_API/$domain")"
  fi

  if [ "$?" != "0" ]; then
    _err "error $domain"
    return 1
  fi
  _debug2 response "$response"
  return 0
}