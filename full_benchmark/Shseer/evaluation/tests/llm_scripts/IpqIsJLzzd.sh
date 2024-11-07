
#!/bin/sh

# Check if the user has provided any command line arguments
if [ $# -eq 0 ]; then
  echo "Usage: $0 [cpu|memory|disk|network]"
  exit 1
fi

# Check the command line argument and gather system information accordingly
case $1 in
  cpu)
    top -bn1 | grep '%Cpu' | awk '{print "CPU Usage: " $2+$4 "%"}'
    ;;
  memory)
    free -m | awk 'NR==2{print "Memory Usage: " $3/$2*100 "%"}'
    ;;
  disk)
    df -h | awk '$NF=="/"{printf "Disk Usage: %d/%dGB (%s)\n", $3,$2,$5}'
    ;;
  network)
    ifconfig | grep 'RX bytes' | awk '{print "Network RX: " $2 " bytes"}'
    ifconfig | grep 'TX bytes' | awk '{print "Network TX: " $6 " bytes"}'
    ;;
  *)
    echo "Invalid option. Usage: $0 [cpu|memory|disk|network]"
    exit 1
    ;;
esac
