# nested objects with user-specified delimiter

# without delimiter
${JO:-jo} a.b=0 a.c.d=1 a.d.e[]=2 a.d.e[]=sam a.c[f]@1 b.e[]g=hi
# with delimiter
${JO:-jo} -d. a.b=0 a.c.d=1 a.d.e[]=2 a.d.e[]=sam a.c[f]@1 b.e[]g=hi
# with more complex delimiter
${JO:-jo} -d\|first_char_only a\|b=0 a\|c\|d=1 a\|d\|e[]=2 a\|d\|e[]=sam a\|c[f]@1 b\|e[]g=hi
