#!/usr/bin/env sh

#Support Microsoft Teams webhooks

#TEAMS_WEBHOOK_URL=""
#TEAMS_THEME_COLOR=""
#TEAMS_SUCCESS_COLOR=""
#TEAMS_ERROR_COLOR=""
#TEAMS_SKIP_COLOR=""

teams_send() {
  _subject="$1"
  _content="$2"
  _statusCode="$3" #0: success, 1: error 2($RENEW_SKIP): skipped
  _debug "_statusCode" "$_statusCode"

  TEAMS_WEBHOOK_URL="${TEAMS_WEBHOOK_URL:-$(_readaccountconf_mutable TEAMS_WEBHOOK_URL)}"
  if [ -z "$TEAMS_WEBHOOK_URL" ]; then
    TEAMS_WEBHOOK_URL=""
    _err "You didn't specify a Microsoft Teams webhook url TEAMS_WEBHOOK_URL yet."
    return 1
  fi
  _saveaccountconf_mutable TEAMS_WEBHOOK_URL "$TEAMS_WEBHOOK_URL"

  TEAMS_THEME_COLOR="${TEAMS_THEME_COLOR:-$(_readaccountconf_mutable TEAMS_THEME_COLOR)}"
  if [ -n "$TEAMS_THEME_COLOR" ]; then
    _saveaccountconf_mutable TEAMS_THEME_COLOR "$TEAMS_THEME_COLOR"
  fi

  TEAMS_SUCCESS_COLOR="${TEAMS_SUCCESS_COLOR:-$(_readaccountconf_mutable TEAMS_SUCCESS_COLOR)}"
  if [ -n "$TEAMS_SUCCESS_COLOR" ]; then
    _saveaccountconf_mutable TEAMS_SUCCESS_COLOR "$TEAMS_SUCCESS_COLOR"
  fi

  TEAMS_ERROR_COLOR="${TEAMS_ERROR_COLOR:-$(_readaccountconf_mutable TEAMS_ERROR_COLOR)}"
  if [ -n "$TEAMS_ERROR_COLOR" ]; then
    _saveaccountconf_mutable TEAMS_ERROR_COLOR "$TEAMS_ERROR_COLOR"
  fi

  TEAMS_SKIP_COLOR="${TEAMS_SKIP_COLOR:-$(_readaccountconf_mutable TEAMS_SKIP_COLOR)}"
  if [ -n "$TEAMS_SKIP_COLOR" ]; then
    _saveaccountconf_mutable TEAMS_SKIP_COLOR "$TEAMS_SKIP_COLOR"
  fi

  export _H1="Content-Type: application/json"

  _subject=$(echo "$_subject" | _json_encode)
  _content=$(echo "$_content" | _json_encode)

  case "$_statusCode" in
    0)
      _color="$TEAMS_SUCCESS_COLOR"
      ;;
    1)
      _color="$TEAMS_ERROR_COLOR"
      ;;
    2)
      _color="$TEAMS_SKIP_COLOR"
      ;;
  esac
################################################################################
# Commit message: feat: add default colors
# Commit URL: https://github.com/acmesh-official/acme.sh/commit/24925a17392147c857d20a6b0272ea7da0bf1843
# Category: more secure code
# Notes: 
# Changed content:
# -   _color="$(echo "${_color:-$TEAMS_THEME_COLOR}" | tr -cd 'a-fA-F0-9')"
# + 
# +   _color=$(echo "$_color" | tr -cd 'a-fA-F0-9')
# +   if [ -z "$_color" ]; then
# +     _color=$(echo "${TEAMS_THEME_COLOR:-$_color_muted}" | tr -cd 'a-fA-F0-9')
# +   fi
################################################################################
# put stream annotation here
# stream enable
  _color="$(echo "${_color:-$TEAMS_THEME_COLOR}" | tr -cd 'a-fA-F0-9')"

  _data="{\"title\": \"$_subject\","
  if [ -n "$_color" ]; then
    _data="$_data\"themeColor\": \"$_color\", "
  fi
  _data="$_data\"text\": \"$_content\"}"

  if _post "$_data" "$TEAMS_WEBHOOK_URL"; then
    # shellcheck disable=SC2154
    if ! _contains "$response" error; then
      _info "teams send success."
      return 0
    fi
  fi
  _err "teams send error."
  _err "$response"
  return 1
}