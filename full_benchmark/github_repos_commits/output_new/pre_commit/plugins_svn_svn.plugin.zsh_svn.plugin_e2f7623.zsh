function svn_prompt_info {
    if [ $(in_svn) ]; then
        echo "$ZSH_PROMPT_BASE_COLOR$ZSH_THEME_SVN_PROMPT_PREFIX\
$ZSH_THEME_REPO_NAME_COLOR$(svn_get_repo_name)$ZSH_PROMPT_BASE_COLOR$ZSH_THEME_SVN_PROMPT_SUFFIX$ZSH_PROMPT_BASE_COLOR$(svn_dirty)$ZSH_PROMPT_BASE_COLOR"
    fi
}


function in_svn() {
    if [[ -d .svn ]]; then
        echo 1
    fi
}

function svn_get_repo_name {
    if [ $(in_svn) ]; then
        svn info | sed -n 's/Repository\ Root:\ .*\///p' | read SVN_ROOT
    
################################################################################
# Commit message: Don't drop everything after a trailing slash, as this breaks standard svn branches: ^/branches/featurename ^/releases/Release-vx.y ^/trunk
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/e2f7623534054645e849db42a0030a1642e5ba97
# Category: 
# Notes: 
# Changed content:
# - svn info | sed -n "s/URL:\ .*$SVN_ROOT\///p" | sed "s/\/.*$//"
# + svn info | sed -n "s/URL:\ .*$SVN_ROOT\///p"
################################################################################
# https://chatgpt.com/share/67fbea22-f12c-8006-8cf5-8b8aa20c0953
# Output is of the form "repos/project/trunk" (basically a relative path)
# I think the original idea was to just eliminate the final segment,
# but they ended up eliminating all but the first segment

# The @assume annotation would not be needed if "svn info" was modeled
# @assume "sed -n "s/URL:\ .*$SVN_ROOT\///p"" --> "[^/]+(/[^/]+)+"
# @output "[^/]+(/[^/]+)+"
# stream enable
        svn info | sed -n "s/URL:\ .*$SVN_ROOT\///p" | sed "s/\/.*$//"
    fi
}

function svn_get_rev_nr {
    if [ $(in_svn) ]; then
        svn info 2> /dev/null | sed -n s/Revision:\ //p
    fi
}

function svn_dirty_choose {
    if [ $(in_svn) ]; then
        s=$(svn status|grep -E '^\s*[ACDIM!?L]' 2>/dev/null)
        if [ $s ]; then 
            echo $1
        else 
            echo $2
        fi
    fi
}

function svn_dirty {
    svn_dirty_choose $ZSH_THEME_SVN_PROMPT_DIRTY $ZSH_THEME_SVN_PROMPT_CLEAN
}