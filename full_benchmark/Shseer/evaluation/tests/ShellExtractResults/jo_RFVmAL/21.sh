# type coercion

# coerce key=val
for v in "" string \"quoted\" 12345 true false null; do
  ${JO:-jo} -- -s s="$v" -n n="$v" -b b="$v" a="$v"
done

# coerce array items
${JO:-jo} -a -- -s 123 -n "This is a test" -b C_Rocks 456

# coercion flag strings should be usable as inputs, when they aren't flags
${JO:-jo} -a -- -s -s -n -n -b -b

# non-flag strings should be read as normal strings, even if they begin with "-"
${JO:-jo} -a -- --test --toast
${JO:-jo} -- --test=--toast

# coercion is one-shot, so all "--toast" strings are normal input
${JO:-jo} -a -- -b --test --toast -s --test --toast -n --test --toast

### These should NOT be coerced

# @ booleans
for v in 0 1; do
  ${JO:-jo} -- -s s@"$v" -n n@"$v" -b b@"$v" a@"$v"
done

# @/% file inclusions
${JO:-jo} -- -s s=@${srcdir:=.}/tests/jo-creator.txt -n n=@${srcdir:=.}/tests/jo-creator.txt -b b=@${srcdir:=.}/tests/jo-creator.txt a=@${srcdir:=.}/tests/jo-creator.txt
${JO:-jo} -- -s s=%${srcdir:=.}/tests/jo-creator.txt -n n=%${srcdir:=.}/tests/jo-creator.txt -b b=%${srcdir:=.}/tests/jo-creator.txt a=%${srcdir:=.}/tests/jo-creator.txt
