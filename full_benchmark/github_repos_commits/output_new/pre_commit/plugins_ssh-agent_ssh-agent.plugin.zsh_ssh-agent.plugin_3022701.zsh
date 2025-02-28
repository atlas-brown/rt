typeset _agent_forwarding _ssh_env_cache

function _start_agent() {
	local lifetime
	local -a identities

	# start ssh-agent and setup environment
	zstyle -s :omz:plugins:ssh-agent lifetime lifetime

	ssh-agent -s ${lifetime:+-t} ${lifetime} | sed 's/^echo/#echo/' >! $_ssh_env_cache
	chmod 600 $_ssh_env_cache
	. $_ssh_env_cache > /dev/null

	# load identies
	zstyle -a :omz:plugins:ssh-agent identities identities

	echo starting ssh-agent...
	ssh-add $HOME/.ssh/${^identities}
}

# Get the filename to store/lookup the environment from
_ssh_env_cache="$HOME/.ssh/environment-$SHORT_HOST"

# test if agent-forwarding is enabled
zstyle -b :omz:plugins:ssh-agent agent-forwarding _agent_forwarding

if [[ $_agent_forwarding == "yes" && -n "$SSH_AUTH_SOCK" ]]; then
	# Add a nifty symlink for screen/tmux if agent forwarding
	[[ -L $SSH_AUTH_SOCK ]] || ln -sf "$SSH_AUTH_SOCK" /tmp/ssh-agent-$USER-screen
elif [[ -f "$_ssh_env_cache" ]]; then
	# Source SSH settings, if applicable
	. $_ssh_env_cache > /dev/null
################################################################################
# Commit message: Use existing ssh-agent when invoking a sudo shell (#3891)  When invoking a shell as root using ```sudo -s```, the ssh-agent plugin starts a new agent although it already exists.  The problem boils down to a check if ssh-agent is running using ```ps x```. If that is extended to ```ps ax``` for root, then the existing ssh-agent will still work.
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/302270174d8173be35e8c1b464a0d9e731650c15
# Category: 
# Notes: 
# Changed content:
# - ps x | grep ssh-agent | grep -q $SSH_AGENT_PID || {
# + ps $FILTER | grep ssh-agent | grep -q $SSH_AGENT_PID || {
################################################################################
# put stream annotation here
# stream enable
	ps x | grep ssh-agent | grep -q $SSH_AGENT_PID || {
		_start_agent
	}
else
	_start_agent
fi

# tidy up after ourselves
unset _agent_forwarding _ssh_env_cache
unfunction _start_agent