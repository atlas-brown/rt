################################################################################
# Commit message: Syncing with the original repo (#2)  * change arvan api script  * change Author name  * change name actor  * Updated --preferred-chain to issue ISRG properly  To support different openssl crl2pkcs7 help cli format  * dnsapi/pdns: also normalize json response in detecting root zone  * Chain (#3408)  * fix https://github.com/acmesh-official/acme.sh/issues/3384 match the issuer to the root CA cert subject  * fix format  * fix https://github.com/acmesh-official/acme.sh/issues/3384  * remove the alt files. https://github.com/acmesh-official/acme.sh/issues/3384  * upgrade freebsd and solaris  * duckdns - fix "integer expression expected" errors (#3397)  * fix "integer expression expected" errors  * duckdns fix  * Update dns_duckdns.sh  * Update dns_duckdns.sh  * Implement smtp notify hook  Support notifications via direct SMTP server connection. Uses Python (2.7.x or 3.4+) to communicate with SMTP server.  * Make shfmt happy  (I'm open to better ways of formatting the heredoc that embeds the Python script.)  * Only save config if send is successful  * Add instructions for reporting bugs  * Prep for curl or Python; clean up SMTP_* variable usage  * Implement curl version of smtp notify-hook  * More than one blank line is an abomination, apparently  I will not try to use whitespace to group code visually  * Fix: Unifi deploy hook support Unifi Cloud Key (#3327)  * fix: unifi deploy hook also update Cloud Key nginx certs  When running on a Unifi Cloud Key device, also deploy to /etc/ssl/private/cloudkey.{crt,key} and reload nginx. This makes the new cert available for the Cloud Key management app running via nginx on port 443 (as well as the port 8443 Unifi Controller app the deploy hook already supported).  Fixes #3326  * Improve settings documentation comments  * Improve Cloud Key pre-flight error messaging  * Fix typo  * Add support for UnifiOS (Cloud Key Gen2)  Since UnifiOS does not use the Java keystore (like a Unifi Controller or Cloud Key Gen1 deploy), this also reworks the settings validation and error messaging somewhat.  * PR review fixes  * Detect unsupported Cloud Key java keystore location  * Don't try to restart inactive services  (and remove extra spaces from reload command)  * Clean up error messages and internal variables  * Change to _getdeployconf/_savedeployconf  * Switch from cp to cat to preserve file permissions  * feat: add huaweicloud error handling  * fix: fix freebsd and solaris  * support openssl 3.0 fix https://github.com/acmesh-official/acme.sh/issues/3399  * make the fix for rsa key only  * Use PROJECT_NAME and VER for X-Mailer header  Also add X-Mailer header to Python version  * Add _clearaccountconf_mutable()  * Rework read/save config to not save default values  Add and use _readaccountconf_mutable_default and _saveaccountconf_mutable_default helpers to capture common default value handling.  New approach also eliminates need for separate underscore-prefixed version of each conf var.  * Implement _rfc2822_date helper  * Clean email headers and warn on unsupported address format  Just in case, make sure CR or NL don't end up in an email header.  * Clarify _readaccountconf_mutable_default  * Add Date email header in Python implementation  * Use email.policy.default in Python 3 implementation  Improves standards compatibility and utf-8 handling in Python 3.3-3.8. (email.policy.default becomes the default in Python 3.9.)  * Prefer Python to curl when both available  * Change default SMTP_SECURE to "tls"  Secure by default. Also try to minimize configuration errors. (Many ESPs/ISPs require STARTTLS, and most support it.)  * Update dns_dp.sh  没有encode中文字符会导致提交失败  * No need to include EC parameters explicitly with the private key. (they are embedded)  * Fixes response handling and thereby allow issuing of subdomain certs  * Adds comment  * fix https://github.com/acmesh-official/acme.sh/issues/3402  * dnsapi/ionos: Use POST instead of PATCH for adding TXT record  The API now supports a POST route for adding records. Therefore checking for already existing records and including them in a PATCH request is no longer necessary.  * fix https://github.com/acmesh-official/acme.sh/issues/3433  * fix https://github.com/acmesh-official/acme.sh/issues/3019  * fix format  * Update dns_servercow.sh to support wildcard certs  Updated dns_servercow.sh to support txt records with multiple entries. This supports wildcard certificates that require txt records with the same name and different contents.  * Update dns_servercow.sh to support wildcard certs  Updated dns_servercow.sh to support txt records with multiple entries. This supports wildcard certificates that require txt records with the same name and different contents.  * fix https://github.com/acmesh-official/acme.sh/issues/3312  * fix format  * feat: add dns_porkbun  * fix: prevent rate limit  Co-authored-by: Vahid Fardi <vahid.fardi@snapp.cab> Co-authored-by: neil <github@neilpang.com> Co-authored-by: Gnought <1684105+gnought@users.noreply.github.com> Co-authored-by: manuel <manuel@mausz.at> Co-authored-by: jerrm <jerrm@users.noreply.github.com> Co-authored-by: medmunds <medmunds@gmail.com> Co-authored-by: Mike Edmunds <github@to.mikeedmunds.com> Co-authored-by: Easton Man <manyang.me@outlook.com> Co-authored-by: czeming <loser_wind@163.com> Co-authored-by: Geert Hendrickx <geert@hendrickx.be> Co-authored-by: Kristian Johansson <kristian.johansson86@gmail.com> Co-authored-by: Lukas Brocke <lukas@brocke.net> Co-authored-by: anom-human <80478363+anom-human@users.noreply.github.com> Co-authored-by: neil <win10@neilpang.com> Co-authored-by: Quentin Dreyer <quentin.dreyer@rgsystem.com>
# Commit URL: https://github.com/acmesh-official/acme.sh/commit/c384ed960c138f4449e79293644c4d0ec937cef1
# Category: 
# Notes: 
# Changed content:
# + #!/usr/bin/env sh
# + 
# + #
# + #PORKBUN_API_KEY="pk1_0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
# + #PORKBUN_SECRET_API_KEY="sk1_0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
# + 
# + PORKBUN_Api="https://porkbun.com/api/json/v3"
# + 
# + ########  Public functions #####################
# + 
# + #Usage: add  _acme-challenge.www.domain.com   "XKrxpRBosdIKFzxW_CT3KLZNf6q0HG9i01zxXp5CPBs"
# + dns_porkbun_add() {
# +   fulldomain=$1
# +   txtvalue=$2
# + 
# +   PORKBUN_API_KEY="${PORKBUN_API_KEY:-$(_readaccountconf_mutable PORKBUN_API_KEY)}"
# +   PORKBUN_SECRET_API_KEY="${PORKBUN_SECRET_API_KEY:-$(_readaccountconf_mutable PORKBUN_SECRET_API_KEY)}"
# + 
# +   if [ -z "$PORKBUN_API_KEY" ] || [ -z "$PORKBUN_SECRET_API_KEY" ]; then
# +     PORKBUN_API_KEY=''
# +     PORKBUN_SECRET_API_KEY=''
# +     _err "You didn't specify a Porkbun api key and secret api key yet."
# +     _err "You can get yours from here https://porkbun.com/account/api."
# +     return 1
# +   fi
# + 
# +   #save the credentials to the account conf file.
# +   _saveaccountconf_mutable PORKBUN_API_KEY "$PORKBUN_API_KEY"
# +   _saveaccountconf_mutable PORKBUN_SECRET_API_KEY "$PORKBUN_SECRET_API_KEY"
# + 
# +   _debug 'First detect the root zone'
# +   if ! _get_root "$fulldomain"; then
# +     return 1
# +   fi
# +   _debug _sub_domain "$_sub_domain"
# +   _debug _domain "$_domain"
# + 
# +   # For wildcard cert, the main root domain and the wildcard domain have the same txt subdomain name, so
# +   # we can not use updating anymore.
# +   #  count=$(printf "%s\n" "$response" | _egrep_o "\"count\":[^,]*" | cut -d : -f 2)
# +   #  _debug count "$count"
# +   #  if [ "$count" = "0" ]; then
# +   _info "Adding record"
# +   if _porkbun_rest POST "dns/create/$_domain" "{\"name\":\"$_sub_domain\",\"type\":\"TXT\",\"content\":\"$txtvalue\",\"ttl\":120}"; then
# +     if _contains "$response" '\"status\":"SUCCESS"'; then
# +       _info "Added, OK"
# +       return 0
# +     elif _contains "$response" "The record already exists"; then
# +       _info "Already exists, OK"
# +       return 0
# +     else
# +       _err "Add txt record error. ($response)"
# +       return 1
# +     fi
# +   fi
# +   _err "Add txt record error."
# +   return 1
# + 
# + }
# + 
# + #fulldomain txtvalue
# + dns_porkbun_rm() {
# +   fulldomain=$1
# +   txtvalue=$2
# + 
# +   PORKBUN_API_KEY="${PORKBUN_API_KEY:-$(_readaccountconf_mutable PORKBUN_API_KEY)}"
# +   PORKBUN_SECRET_API_KEY="${PORKBUN_SECRET_API_KEY:-$(_readaccountconf_mutable PORKBUN_SECRET_API_KEY)}"
# + 
# +   _debug 'First detect the root zone'
# +   if ! _get_root "$fulldomain"; then
# +     return 1
# +   fi
# +   _debug _sub_domain "$_sub_domain"
# +   _debug _domain "$_domain"
# + 
# +   count=$(echo "$response" | _egrep_o "\"count\": *[^,]*" | cut -d : -f 2 | tr -d " ")
# +   _debug count "$count"
# +   if [ "$count" = "0" ]; then
# +     _info "Don't need to remove."
# +   else
# +     record_id=$(echo "$response" | tr '{' '\n' | grep "$txtvalue" | cut -d, -f1 | cut -d: -f2 | tr -d \")
# +     _debug "record_id" "$record_id"
# +     if [ -z "$record_id" ]; then
# +       _err "Can not get record id to remove."
# +       return 1
# +     fi
# +     if ! _porkbun_rest POST "dns/delete/$_domain/$record_id"; then
# +       _err "Delete record error."
# +       return 1
# +     fi
# +     echo "$response" | tr -d " " | grep '\"status\":"SUCCESS"' >/dev/null
# +   fi
# + 
# + }
# + 
# + ####################  Private functions below ##################################
# + #_acme-challenge.www.domain.com
# + #returns
# + # _sub_domain=_acme-challenge.www
# + # _domain=domain.com
# + _get_root() {
# +   domain=$1
# +   i=1
# +   while true; do
# +     h=$(printf "%s" "$domain" | cut -d . -f $i-100)
# +     _debug h "$h"
# +     if [ -z "$h" ]; then
# +       return 1
# +     fi
# + 
# +     if _porkbun_rest POST "dns/retrieve/$h"; then
# +       if _contains "$response" "\"status\":\"SUCCESS\""; then
# +         _sub_domain="$(echo "$fulldomain" | sed "s/\\.$_domain\$//")"
# +         _domain=$h
# +         return 0
# +       else
# +         _debug "Go to next level of $_domain"
# +       fi
# +     else
# +       _debug "Go to next level of $_domain"
# +     fi
# +     i=$(_math "$i" + 1)
# +   done
# + 
# +   return 1
# + }
# + 
# + _porkbun_rest() {
# +   m=$1
# +   ep="$2"
# +   data="$3"
# +   _debug "$ep"
# + 
# +   api_key_trimmed=$(echo "$PORKBUN_API_KEY" | tr -d '"')
# +   secret_api_key_trimmed=$(echo "$PORKBUN_SECRET_API_KEY" | tr -d '"')
# + 
# +   test -z "$data" && data="{" || data="$(echo $data | cut -d'}' -f1),"
# +   data="$data\"apikey\":\"$api_key_trimmed\",\"secretapikey\":\"$secret_api_key_trimmed\"}"
# + 
# +   export _H1="Content-Type: application/json"
# + 
# +   if [ "$m" != "GET" ]; then
# +     _debug data "$data"
# +     response="$(_post "$data" "$PORKBUN_Api/$ep" "" "$m")"
# +   else
# +     response="$(_get "$PORKBUN_Api/$ep")"
# +   fi
# + 
# +   _sleep 3 # prevent rate limit
# + 
# +   if [ "$?" != "0" ]; then
# +     _err "error $ep"
# +     return 1
# +   fi
# +   _debug2 response "$response"
# +   return 0
# + }
################################################################################
# put stream annotation here
# stream enable
#!/usr/bin/env sh

#
#PORKBUN_API_KEY="pk1_0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
#PORKBUN_SECRET_API_KEY="sk1_0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

PORKBUN_Api="https://porkbun.com/api/json/v3"

########  Public functions #####################

#Usage: add  _acme-challenge.www.domain.com   "XKrxpRBosdIKFzxW_CT3KLZNf6q0HG9i01zxXp5CPBs"
dns_porkbun_add() {
  fulldomain=$1
  txtvalue=$2

  PORKBUN_API_KEY="${PORKBUN_API_KEY:-$(_readaccountconf_mutable PORKBUN_API_KEY)}"
  PORKBUN_SECRET_API_KEY="${PORKBUN_SECRET_API_KEY:-$(_readaccountconf_mutable PORKBUN_SECRET_API_KEY)}"

  if [ -z "$PORKBUN_API_KEY" ] || [ -z "$PORKBUN_SECRET_API_KEY" ]; then
    PORKBUN_API_KEY=''
    PORKBUN_SECRET_API_KEY=''
    _err "You didn't specify a Porkbun api key and secret api key yet."
    _err "You can get yours from here https://porkbun.com/account/api."
    return 1
  fi

  #save the credentials to the account conf file.
  _saveaccountconf_mutable PORKBUN_API_KEY "$PORKBUN_API_KEY"
  _saveaccountconf_mutable PORKBUN_SECRET_API_KEY "$PORKBUN_SECRET_API_KEY"

  _debug 'First detect the root zone'
  if ! _get_root "$fulldomain"; then
    return 1
  fi
  _debug _sub_domain "$_sub_domain"
  _debug _domain "$_domain"

  # For wildcard cert, the main root domain and the wildcard domain have the same txt subdomain name, so
  # we can not use updating anymore.
  #  count=$(printf "%s\n" "$response" | _egrep_o "\"count\":[^,]*" | cut -d : -f 2)
  #  _debug count "$count"
  #  if [ "$count" = "0" ]; then
  _info "Adding record"
  if _porkbun_rest POST "dns/create/$_domain" "{\"name\":\"$_sub_domain\",\"type\":\"TXT\",\"content\":\"$txtvalue\",\"ttl\":120}"; then
    if _contains "$response" '\"status\":"SUCCESS"'; then
      _info "Added, OK"
      return 0
    elif _contains "$response" "The record already exists"; then
      _info "Already exists, OK"
      return 0
    else
      _err "Add txt record error. ($response)"
      return 1
    fi
  fi
  _err "Add txt record error."
  return 1

}

#fulldomain txtvalue
dns_porkbun_rm() {
  fulldomain=$1
  txtvalue=$2

  PORKBUN_API_KEY="${PORKBUN_API_KEY:-$(_readaccountconf_mutable PORKBUN_API_KEY)}"
  PORKBUN_SECRET_API_KEY="${PORKBUN_SECRET_API_KEY:-$(_readaccountconf_mutable PORKBUN_SECRET_API_KEY)}"

  _debug 'First detect the root zone'
  if ! _get_root "$fulldomain"; then
    return 1
  fi
  _debug _sub_domain "$_sub_domain"
  _debug _domain "$_domain"

  count=$(echo "$response" | _egrep_o "\"count\": *[^,]*" | cut -d : -f 2 | tr -d " ")
  _debug count "$count"
  if [ "$count" = "0" ]; then
    _info "Don't need to remove."
  else
    record_id=$(echo "$response" | tr '{' '\n' | grep "$txtvalue" | cut -d, -f1 | cut -d: -f2 | tr -d \")
    _debug "record_id" "$record_id"
    if [ -z "$record_id" ]; then
      _err "Can not get record id to remove."
      return 1
    fi
    if ! _porkbun_rest POST "dns/delete/$_domain/$record_id"; then
      _err "Delete record error."
      return 1
    fi
    echo "$response" | tr -d " " | grep '\"status\":"SUCCESS"' >/dev/null
  fi

}

####################  Private functions below ##################################
#_acme-challenge.www.domain.com
#returns
# _sub_domain=_acme-challenge.www
# _domain=domain.com
_get_root() {
  domain=$1
  i=1
  while true; do
    h=$(printf "%s" "$domain" | cut -d . -f $i-100)
    _debug h "$h"
    if [ -z "$h" ]; then
      return 1
    fi

    if _porkbun_rest POST "dns/retrieve/$h"; then
      if _contains "$response" "\"status\":\"SUCCESS\""; then
        _sub_domain="$(echo "$fulldomain" | sed "s/\\.$_domain\$//")"
        _domain=$h
        return 0
      else
        _debug "Go to next level of $_domain"
      fi
    else
      _debug "Go to next level of $_domain"
    fi
    i=$(_math "$i" + 1)
  done

  return 1
}

_porkbun_rest() {
  m=$1
  ep="$2"
  data="$3"
  _debug "$ep"

  api_key_trimmed=$(echo "$PORKBUN_API_KEY" | tr -d '"')
  secret_api_key_trimmed=$(echo "$PORKBUN_SECRET_API_KEY" | tr -d '"')

  test -z "$data" && data="{" || data="$(echo $data | cut -d'}' -f1),"
  data="$data\"apikey\":\"$api_key_trimmed\",\"secretapikey\":\"$secret_api_key_trimmed\"}"

  export _H1="Content-Type: application/json"

  if [ "$m" != "GET" ]; then
    _debug data "$data"
    response="$(_post "$data" "$PORKBUN_Api/$ep" "" "$m")"
  else
    response="$(_get "$PORKBUN_Api/$ep")"
  fi

  _sleep 3 # prevent rate limit

  if [ "$?" != "0" ]; then
    _err "error $ep"
    return 1
  fi
  _debug2 response "$response"
  return 0
}