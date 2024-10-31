# Query: Retrieve only build number of current kernel, ie. #104

uname -v | grep -o '#[0-9]\+'