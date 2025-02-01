_mix_refresh () {
  if [ -f .mix_tasks ]; then
    rm .mix_tasks
  fi
  echo "Generating .mix_tasks..." > /dev/stderr
  _mix_generate
  cat .mix_tasks
}

_mix_does_task_list_need_generating () {
  [ ! -f .mix_tasks ];
}

_mix_generate () {
################################################################################
# Commit message: Fix mix-fast plugin (#6708)  The mix command for listing all available actions has been changed from `mix --help` to `mix help`.
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/bf87e99a14320885c506c6b07c9ead8825ee53b9
# Category: about refactor
# Notes: 
# Changed content:
# -   mix --help | grep -v 'iex -S' | tail -n +2 | cut -d " " -f 2 > .mix_tasks
# +   mix help | grep -v 'iex -S' | tail -n +2 | cut -d " " -f 2 > .mix_tasks
################################################################################
# put stream annotation here
# stream enable
  mix help | grep -v 'iex -S' | tail -n +2 | cut -d " " -f 2 > .mix_tasks
}

_mix () {
  if [ -f mix.exs ]; then
    if _mix_does_task_list_need_generating; then
      echo "\nGenerating .mix_tasks..." > /dev/stderr
      _mix_generate
    fi
    compadd `cat .mix_tasks`
  fi
}

compdef _mix mix
alias mix_refresh='_mix_refresh'