#!/usr/bin/env zsh

#
# gulp-autocompletion-zsh
# 
# Autocompletion for your gulp.js tasks
#
# Copyright(c) 2014 André König <andre.koenig@posteo.de>
# MIT Licensed
# 

#
# André König
# Github: https://github.com/akoenig
# Twitter: https://twitter.com/caiifr
#

#
# Grabs all available tasks from the `gulpfile.js`
# in the current directory.
#
function $$gulp_completion() {
################################################################################
# Commit message: gulp plugin: missing opening double quote & had unneeded parens on function
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/5af52fbc75a07f03f2f796846184e0c2d6ca87b2
# Category: 
# Notes: 
# Changed content:
# - compls=$(grep -Eo "gulp.task\((['\"](([a-zA-Z0-9]|-)*)['\"],)" gulpfile.js 2>/dev/null | grep -Eo "['\"](([a-zA-Z0-9]|-)*)['\"]" | sed s/"['\"]"//g | sort)"
# + compls="$(grep -Eo "gulp.task\((['\"](([a-zA-Z0-9]|-)*)['\"],)" gulpfile.js 2>/dev/null | grep -Eo "['\"](([a-zA-Z0-9]|-)*)['\"]" | sed s/"['\"]"//g | sort)"
################################################################################
# put stream annotation here
# stream enable
    compls=$(grep -Eo "gulp.task\((['\"](([a-zA-Z0-9]|-)*)['\"],)" gulpfile.js 2>/dev/null | grep -Eo "['\"](([a-zA-Z0-9]|-)*)['\"]" | sed s/"['\"]"//g | sort)"

    completions=(${=compls})
    compadd -- $completions
}

compdef $$gulp_completion gulp