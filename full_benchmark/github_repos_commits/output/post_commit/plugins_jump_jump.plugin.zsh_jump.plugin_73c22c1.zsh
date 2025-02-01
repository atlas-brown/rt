# Easily jump around the file system by manually adding marks
# marks are stored as symbolic links in the directory $MARKPATH (default $HOME/.marks)
#
# jump FOO: jump to a mark named FOO
# mark FOO: create a mark named FOO
# unmark FOO: delete a mark
# marks: lists all marks
#
export MARKPATH=$HOME/.marks
function jump { 
################################################################################
# Commit message: Add tab completion for jump plugin
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/73c22c146c57afe5c9ce341cff876abf00571463
# Category: more secure code
# Notes: 
# Changed content:
# - 	cd -P $MARKPATH/$1 2>/dev/null || echo "No such mark: $1"
# + 	cd -P "$MARKPATH/$1" 2>/dev/null || echo "No such mark: $1"
################################################################################
# put stream annotation here
# stream enable
	cd -P "$MARKPATH/$1" 2>/dev/null || echo "No such mark: $1"
}
function mark { 
	mkdir -p "$MARKPATH"; ln -s "$(pwd)" $MARKPATH/$1
}
function unmark { 
	rm -i "$MARKPATH/$1"
}
function marks {
################################################################################
# Commit message: Add tab completion for jump plugin
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/73c22c146c57afe5c9ce341cff876abf00571463
# Category: more secure code
# Notes: 
# Changed content:
# - 	ls -l $MARKPATH | sed 's/  / /g' | cut -d' ' -f9- | sed 's/ -/\t-/g' && echo
# + 	ls -l "$MARKPATH" | sed 's/  / /g' | cut -d' ' -f9- | sed 's/ -/\t-/g' && echo
################################################################################
# put stream annotation here
# stream enable
	ls -l "$MARKPATH" | sed 's/  / /g' | cut -d' ' -f9- | sed 's/ -/\t-/g' && echo
}

function _completemarks {
  reply=($(ls $MARKPATH))
}

compctl -K _completemarks jump
compctl -K _completemarks unmark