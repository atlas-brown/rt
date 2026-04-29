_rake_does_task_list_need_generating () {
  [[ ! -f .rake_tasks ]] || [[ Rakefile -nt .rake_tasks ]] || { _is_rails_app && _tasks_changed }
}

_is_rails_app () {
  [[ -e "bin/rails" ]] || [[ -e "script/rails" ]]
}

_tasks_changed () {
  local -a files
  files=(lib/tasks lib/tasks/**/*(N))

  for file in $files; do
    if [[ "$file" -nt .rake_tasks ]]; then
      return 0
    fi
  done

  return 1
}

_rake_generate () {
################################################################################
# Commit message: rake-fast: remove brackets from completion entries  Fixes #5653
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/c56fa996e7cb1500dca97723d525e4c97af33c75
# Category: 
# Notes: 
# Changed content:
# - rake --silent --tasks | cut -d " " -f 2 > .rake_tasks
# + rake --silent --tasks | cut -d " " -f 2 | sed 's/\[.*\]//g' > .rake_tasks
################################################################################
# https://www.rubyguides.com/2019/02/ruby-rake/
# https://chatgpt.com/c/67fa811b-aa9c-8006-96a6-71976dee2069
# I'm not sure if the developers were aware of the existence of brackets in the output or not.
# @assume "rake --silent --tasks" --> "rake [a-z:]+(\[[^ ]*\])?"
# @assume "sed 's/\[.*\]//g' > .rake_tasks" --> "[a-z:]+"
# @output "[a-z:]+"
# stream enable
  rake --silent --tasks | cut -d " " -f 2 | sed 's/\[.*\]//g' > .rake_tasks
}

_rake () {
  if [[ -f Rakefile ]]; then
    if _rake_does_task_list_need_generating; then
      echo "\nGenerating .rake_tasks..." >&2
      _rake_generate
    fi
    compadd $(cat .rake_tasks)
  fi
}
compdef _rake rake

rake_refresh () {
  [[ -f .rake_tasks ]] && rm -f .rake_tasks

  echo "Generating .rake_tasks..." >&2
  _rake_generate
  cat .rake_tasks
}
