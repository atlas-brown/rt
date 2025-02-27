function gi() { curl -L https://www.gitignore.io/api/$@ ;}

_gitignoreio_get_command_list() {
################################################################################
# Commit message: Follow-redirect and silent mode curl throughout gitignore  This commit completes previous efforts and standardizes both curl commands into using silent mode and following redirects in case the URL changes again in the future.
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/b452cafb163cde6619ac741027251bed2709f78e
# Category: 
# Notes: 
# Changed content:
# -   curl -s https://www.gitignore.io/api/list | tr "," "\n"
# +   curl -sL https://www.gitignore.io/api/list | tr "," "\n"
################################################################################
# put stream annotation here
# stream enable
  curl -s https://www.gitignore.io/api/list | tr "," "\n"
}

_gitignoreio () {
  compset -P '*,'
  compadd -S '' `_gitignoreio_get_command_list`
}

compdef _gitignoreio gi