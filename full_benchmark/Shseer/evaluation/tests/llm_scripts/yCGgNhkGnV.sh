
#!/bin/sh

inputString=$1
stringLength=$(echo -n $inputString | wc -c)
echo "Length of the string is: $stringLength"
