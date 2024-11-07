
logFile="logfile.txt"
patterns=("pattern1" "pattern2" "pattern3")

if [ -f $logFile ]; then
    for pattern in "${patterns[@]}"; do
        count=$(grep -c $pattern $logFile)
        echo "Pattern $pattern occurs $count times"
        grep $pattern $logFile | awk '{print $2, $3}'
    done
else
    echo "Log file does not exist"
fi
