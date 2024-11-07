#!/bin/bash
echo "$(figlet EASY-CVE)" "By ABIS" 
echo "Twiiter: SirL0gic"
echo
echo
echo "1)Simple Scan 2)Heavy Scan 3)Light Vulnerablity Scan 4)Heavy Vulnerablity Scan"
read -p "Choose an option:" option 
echo


if [ $option = "1" ]
    then
    read -p  "Enter IP: " ip
    echo "$(nmap $ip)" 

elif [ $option = "2" ]
    then
    read -p  "Enter IP: " ip
    read -p "Port? y/n: " portoption

    if [ $portoption = "y" ]
        then
        read -p  "Enter Port: " port
        echo "$(nmap -A $ip -p $port)" 
    else
        echo "$(nmap -A $ip)" 
        fi
        
        
elif [ $option = "3" ]
    then
    read -p  "Enter IP: " ip
    echo "$(nmap  -Pn --script=vulners.nse $ip)" 
    

elif [ $option = "4" ]
    then
    read -p  "Enter IP: " ip
    read -p "Port? y/n: " portoption

    if [ $portoption = "y" ]
        then
        read -p  "Enter Port: " port
        read -p "Save results? y/n: " save
        
             if [ $save = "y" ]
                then
                read -p  "Location: " savelocation
                echo "$(nmap -oN $savelocation -sV --script=vulscan/vulscan.nse $ip -p $port)" 
            else
                echo "$(nmap -sV --script=vulscan/vulscan.nse $ip -p $port)" 
                fi
            
       
    else
            read -p "Save results? y/n: " save
            if [ $save = "y" ]
                    then
                    read -p  "Location: " savelocation
                    echo "$(nmap -oN $savelocation -sV --script=vulscan/vulscan.nse $ip)" 
                else
                    echo "$(nmap -sV --script=vulscan/vulscan.nse $ip)" 
                    fi
fi
fi

echo "BYE BYE"



