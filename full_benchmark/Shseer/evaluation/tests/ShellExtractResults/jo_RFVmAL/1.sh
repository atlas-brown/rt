# read nested json elements

echo '{"a":1,"b":"val"}' > $$.1

${JO:-jo} nested=:$$.1

# nested json within object path
${JO:-jo} -d . top.obj1.c=3 top.obj1.d="key" top.obj2=:$$.1

rm -f $$.1
