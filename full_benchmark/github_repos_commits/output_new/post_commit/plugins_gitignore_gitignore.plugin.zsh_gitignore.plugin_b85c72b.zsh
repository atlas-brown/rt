function gi() { curl -fL https://www.gitignore.io/api/${(j:,:)@} }

_gitignoreio_get_command_list() {
################################################################################
# Commit message: Better app error handling in curl (#5828)  Deals with app error page, saving true error instead.  Upon app failure, Heroku returns HTML "Application Error" page. Finding HTML page in .gitignore is confusing, so I replaced `-s` with `-f` in curl calls, which cuts such output.  Replace instead of addition as no progress meter outputs either.  It is practically impossible to teach good programming style to students that have had prior exposure to BASIC.  As potential programmers, they are mentally mutilated beyond hope of regeneration.       -- E. W. Dijkstra
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/b85c72b5f6ed1d33414cc2d9e7afceef12b861e7
# Category: 
# Notes: 
# Changed content:
# - curl -sL https://www.gitignore.io/api/list | tr "," "\n"
# + curl -fL https://www.gitignore.io/api/list | tr "," "\n"
################################################################################
# put stream annotation here
# stream enable
  curl -fL https://www.gitignore.io/api/list | tr "," "\n"
}

_gitignoreio () {
  compset -P '*,'
  compadd -S '' `_gitignoreio_get_command_list`
}

compdef _gitignoreio gi