# Homestead basic command completion
_homestead_get_command_list () {
################################################################################
# Commit message: homestead: repair sed regex (#8103)
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/08beebd89f9eec956c126c732a287ec5a5a197a8
# Category: 
# Notes: 
# Changed content:
# -   homestead --no-ansi | sed "1,/(Available|Common) commands/d" | awk '/^ +[a-z]+/ { print $1 }'
# +   homestead --no-ansi | sed -E "1,/(Available|Common) commands/d" | awk '/^ +[a-z]+/ { print $1 }'
################################################################################
# put stream annotation here
# stream enable
  homestead --no-ansi | sed -E "1,/(Available|Common) commands/d" | awk '/^ +[a-z]+/ { print $1 }'
}

_homestead () {
  compadd `_homestead_get_command_list`
}

compdef _homestead homestead