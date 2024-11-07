# user-friendly errors
${JO:-jo} b[]=1 b[]=2
${JO:-jo} b[]=1 b[a]=3 2>&1 || echo "Test 2 should fail"

${JO:-jo} d[m]=10 d[n]=20
${JO:-jo} d[m]=10 d[]=20 2>&1 || echo "Test 4 should fail"
