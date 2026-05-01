# Query: Retrieve only build number of current kernel, ie. #104

uname -r | awk -F'-' '{print $2}'