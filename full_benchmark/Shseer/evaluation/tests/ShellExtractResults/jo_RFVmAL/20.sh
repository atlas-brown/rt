# disable creation of null-valued keys

${JO:-jo} foo=
${JO:-jo} -n foo=
${JO:-jo} foo=1 bar= baz=3
${JO:-jo} -n foo=1 bar= baz=3
nothing=
${JO:-jo} list[]=1 list[]=$nothing
${JO:-jo} -n list[]=1 list[]=$nothing

