# Query: Retrieve only build number of current kernel, ie. #104

# @output "#[0-9]+"
uname -v | grep -o '#[0-9]\+'
