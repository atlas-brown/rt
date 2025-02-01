# The version of the format of .rake_tasks. If the output of _rake_generate
# changes, incrementing this number will force it to regenerate
_rake_tasks_version=2

_rake_does_task_list_need_generating () {
################################################################################
# Commit message: feat(rake-fast): show task descriptions in autocomplete (#11653)
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/dab09cc0eec220f5c1a541ccb75449c62c20bdb4
# Category: may be detected by annotations + cut/tr/sed procedures
# Notes: 
# Changed content:
# -   [[ ! -f .rake_tasks ]] || [[ Rakefile -nt .rake_tasks ]] || { _is_rails_app && _tasks_changed }
# +   _rake_tasks_missing || _rake_tasks_version_changed || _rakefile_has_changes || { _is_rails_app && _tasks_changed }
# + }
# + 
# + _rake_tasks_missing () {
# +   [[ ! -f .rake_tasks ]]
# + }
# + 
# + _rake_tasks_version_changed () {
# +   local -a file_version
# +   file_version=`head -n 1 .rake_tasks | sed "s/^version\://"`
# + 
# +   if ! [[ $file_version =~ '^[0-9]*$' ]]; then
# +     return true
# +   fi
# + 
# +   [[ $file_version -ne $_rake_tasks_version ]]
# + }
# + 
# + _rakefile_has_changes () {
# +   [[ Rakefile -nt .rake_tasks ]]
################################################################################
# put stream annotation here
# stream enable
  _rake_tasks_missing || _rake_tasks_version_changed || _rakefile_has_changes || { _is_rails_app && _tasks_changed }
}

_rake_tasks_missing () {
  [[ ! -f .rake_tasks ]]
}

_rake_tasks_version_changed () {
  local -a file_version
  file_version=`head -n 1 .rake_tasks | sed "s/^version\://"`

  if ! [[ $file_version =~ '^[0-9]*$' ]]; then
    return true
  fi

  [[ $file_version -ne $_rake_tasks_version ]]
}

_rakefile_has_changes () {
  [[ Rakefile -nt .rake_tasks ]]
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
# Commit message: feat(rake-fast): show task descriptions in autocomplete (#11653)
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/dab09cc0eec220f5c1a541ccb75449c62c20bdb4
# Category: may be detected by annotations + cut/tr/sed procedures
# Notes: 
# Changed content:
# -   rake --silent --tasks | cut -d " " -f 2 | sed 's/\[.*\]//g' > .rake_tasks
# +   echo "version:$_rake_tasks_version" > .rake_tasks
# + 
# +   rake --silent --tasks --all \
# +     | sed "s/^rake //" | sed "s/\:/\\\:/g" \
# +     | sed "s/\[[^]]*\]//g" \
# +     | sed "s/ *# /\:/" \
# +     | sed "s/\:$//" \
# +     >> .rake_tasks
################################################################################
# put stream annotation here
# stream enable
  echo "version:$_rake_tasks_version" > .rake_tasks

  rake --silent --tasks --all \
    | sed "s/^rake //" | sed "s/\:/\\\:/g" \
    | sed "s/\[[^]]*\]//g" \
    | sed "s/ *# /\:/" \
    | sed "s/\:$//" \
    >> .rake_tasks
}

_rake () {
  if [[ -f Rakefile ]]; then
    if _rake_does_task_list_need_generating; then
      echo "\nGenerating .rake_tasks..." >&2
      _rake_generate
    fi
    local -a rake_options
    rake_options=("${(@f)$(cat .rake_tasks)}")
    shift rake_options
    _describe 'rake tasks' rake_options
  fi
}
compdef _rake rake

rake_refresh () {
  [[ -f .rake_tasks ]] && rm -f .rake_tasks

  echo "Generating .rake_tasks..." >&2
  _rake_generate
  cat .rake_tasks
}