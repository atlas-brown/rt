
#!/bin/sh

# Check if the user has provided an input
if [ -z "$1" ]; then
  echo "Usage: $0 <prefix_math_expression>"
  exit 1
fi

# Read the prefix math expression from the command line
expression="$1"

# Define a function to evaluate the prefix math expression
evaluate_expression() {
  local op=$1
  local num1=$2
  local num2=$3
  case $op in
    "+") echo $(($num1 + $num2));;
    "-") echo $(($num1 - $num2));;
    "*") echo $(($num1 * $num2));;
    "/") echo $(($num1 / $num2));;
    *) echo "Invalid operator";;
  esac
}

# Use a stack to parse and evaluate the prefix math expression
stack=()
for token in $(echo $expression | tr ' ' '\n' | tac); do
  if [ "$token" -eq "$token" ] 2>/dev/null; then
    stack+=($token)
  else
    num1=${stack[-1]}
    num2=${stack[-2]}
    stack=("${stack[@]:0:$((${#stack[@]}-2))}")
    result=$(evaluate_expression $token $num1 $num2)
    stack+=($result)
  fi
done

# Print the result
echo "Result: ${stack[0]}"
