encode64(){ echo -n $1 | base64 }
################################################################################
# Commit message: Modified to use full parameter as newer versions of base64 uses lowercase D
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/6c6072c492064abf613fc1b89b4d635020631ef4
# Category: about refactor
# Notes: 
# Changed content:
# - decode64(){ echo -n $1 | base64 -D }
# + decode64(){ echo -n $1 | base64 --decode }
################################################################################
# put stream annotation here
# stream enable
decode64(){ echo -n $1 | base64 -D }
alias e64=encode64
alias d64=decode64