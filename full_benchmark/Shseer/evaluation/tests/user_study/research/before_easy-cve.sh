#!/bin/bash
echo "$(figlet EASY-CVE)" "By ABIS" 
echo "Twiiter: SirL0gic"
echo
echo
echo "1)Light Vulnerablity Scan"
echo "2)Heavy Vulnerablity Scan"
echo 
read -p "Choose an option:" option 
echo
echo


        
if [ $option = "1" ]
    then
    read -p  "[+]Enter IP: " ip
    read -p "[+]Port? y/n: " portoption

    if [ $portoption = "y" ]
        then
        read -p  "[+]Enter Port: " port
        read -p "[+]Save results? y/n: " save
        
             if [ $save = "y" ]
                then
                read -p  "[+]Location: " savelocation
                echo "$(nmap -oN $savelocation -Pn -sV -A --script=vulners.nse $ip -p $port)" 
            else
                echo "$(nmap -Pn  -sV -A --script=vulners.nse $ip -p $port)" 
                fi
            
       
    else
            read -p "[+]Save results? y/n: " save
            if [ $save = "y" ]
                    then
                    read -p  "[+]Location: " savelocation
                    echo "$(nmap -Pn  -oN $savelocation -sV -A --script=vulners.nse $ip)" 
                else
                    echo "$(nmap -Pn  -sV -A --script=vulners.nse $ip)" 
                    fi
fi
    

elif [ $option = "2" ]
    then
    read -p  "[+]Enter IP: " ip
    read -p "[+]Port? y/n: " portoption

    if [ $portoption = "y" ]
        then
        read -p  "[+]Enter Port: " port
        read -p "[+]Save results? y/n: " save
        
             if [ $save = "y" ]
                then
                read -p  "[+]Location: " savelocation
                echo "$(nmap -oN $savelocation -Pn  -sV -A --script=vulscan/vulscan.nse $ip -p $port)" 
            else
                echo "$(nmap -sV -A -Pn  --script=vulscan/vulscan.nse $ip -p $port)" 
                fi
            
       
    else
            read -p "[+]Save results? y/n: " save
            if [ $save = "y" ]
                    then
                    read -p  "[+]Location: " savelocation
                    echo "$(nmap -oN $savelocation -Pn  -sV -A --script=vulscan/vulscan.nse $ip)" 
                else
                    echo "$(nmap -sV -A -Pn  --script=vulscan/vulscan.nse $ip)" 
                    fi
fi
fi

echo "BYE BYE"





