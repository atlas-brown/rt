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
	cd -P "$MARKPATH/$1" 2>/dev/null || echo "No such mark: $1"
}
function mark {
	mkdir -p "$MARKPATH"; ln -s "$(pwd)" $MARKPATH/$1
}
function unmark {
	rm -i "$MARKPATH/$1"
}
function marks {
	ls -l "$MARKPATH" | sed 's/  / /g' | cut -d' ' -f9- | sed 's/ -/\t-/g' && echo
}

function _completemarks {
################################################################################
# Commit message: Better filename matching
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/a265acee4f991dfd96fb3a9057309e9c1a345a2c
# Category: hard sed
# Notes: 
# Changed content:
# -   reply=($(ls $MARKPATH/**/*(-) | grep : | sed -E 's/(.*)\/([a-z]*):$/\2/g'))
# +   reply=($(ls $MARKPATH/**/*(-) | grep : | sed -E 's/(.*)\/([_\da-zA-Z\-]*):$/\2/g'))
################################################################################
# put stream annotation here
# stream enable
  reply=($(ls $MARKPATH/**/*(-) | grep : | sed -E 's/(.*)\/([a-z]*):$/\2/g'))
}

compctl -K _completemarks jump
compctl -K _completemarks unmark