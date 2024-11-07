# nested with executable
${JO:-jo} name="Jane Jolie" data="$(${JO:-jo} age= country=ES)"

# the double quotes around data are required for OpenBSD 5.8
# which mucks up the input with its pdksh otherwise
