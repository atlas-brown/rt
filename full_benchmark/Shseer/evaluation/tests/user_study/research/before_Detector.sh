#!/bin/bash

#sudo date -s "Sat Aug  13 15:55:11 PDT 2016"
#sudo date -s "Sat Aug  13 15:55:11 UTC 2016" # During Daylight savings time
#cd /home/francesco/Dropbox/EH/Software/My_Code/Version_3_Light/

reqtemp(){ #Temp sensor
	sudo gatttool -b $ID --char-write-req -a 0x24 -n $Action_1 >/dev/null 2>&1 #initiates (0x24)  # write 52: second byte (1) indicates the PIR_on_off and 1 means on, while the second byte (5) says 5 mins sleep time
	sleep 1.1
	tempOutput="$(sudo gatttool -b $ID --char-read -a 0x21)" #collects (0x21)
	sleep 0.1
	sudo gatttool -b $ID --char-write-req -a 0x24 -n 00 >/dev/null 2>&1 #disables (0x24)

	# Manipulating data
	outputPrefix="Characteristic value/descriptor: "
	raw_temp_data=${tempOutput#$outputPrefix} #Removes prefix of tempOutput
	#/bin/echo ${raw_temp_data} # raw temp bytes from sensortag
	info="$(python conversion_func.py info "${raw_temp_data}")" # Converts raw_temp_data to celsius
        IFS='|' read -ra ADDR <<< "$info"

        perf=${ADDR[0]}
        batt=${ADDR[1]}
        PIR=${ADDR[2]}
        reed=${ADDR[3]}
        light=${ADDR[4]}
        info=${ADDR[5]}
}
reqlux(){	#Lux sensor
	echo "Reading Light..."
	sudo gatttool -b $ID --char-write-req -a 0x44 -n 01 #initiates (0x44)
	sleep 1
	luxOutput="$(sudo gatttool -b $ID --char-read -a 0x41)" #collects 0x41)
	sleep 0.5
	sudo gatttool -b $ID --char-write-req -a 0x44 -n 00 #disables (0x44)
	sleep 0.5

	# Manipulating data
	outputPrefix="Characteristic value/descriptor: "
	raw_lux_data=${luxOutput#$outputPrefix} #Removes prefix of luxOutput
	/bin/echo ${raw_lux_data} # raw lux bytes from sensortag
	lux="$(python lux_conversion.py "${raw_lux_data}")" # Converts raw_lux_data to lux
}

reqhum(){	#Humidity sensor
	sudo gatttool -b $ID --char-write-req -a 0x2C -n $Action_2 > /dev/null 2>&1 #initiates (0x44)
	sleep 1.1
	HumOutput="$(sudo gatttool -b $ID --char-read -a 0x29)" #collects 0x41)
	sleep 0.1
	sudo gatttool -b $ID --char-write-req -a 0x2C -n 00 > /dev/null 2>&1 #disables (0x44)

	# Manipulating data
	outputPrefix="Characteristic value/descriptor: "
	raw_hum_data=${HumOutput#$outputPrefix} #Removes prefix of luxOutput
	#raw_hum_data="d0 5f 78 89"
	#/bin/echo "hum_raw_data: " ${raw_hum_data} # raw hum bytes from sensortag
	hum="$(python conversion_func.py hum "${raw_hum_data}")" # Converts raw_hum_data to celsius
	IFS='|' read -ra ADDR <<< "$hum"
	
	temp_hum_sens=${ADDR[0]}
	hum_hum_sens=${ADDR[1]}
}

#reqinfo(){
#	#echo "Reading " $Name
#	sudo gatttool -b $ID --char-write-req -a 0x34 -n $Action_1 > useless.txt #initiates (0x44)
#	sleep 1.1
#	infoOutput="$(sudo gatttool -b $ID --char-read -a 0x31)" #collects 0x41)
#	sleep 0.5
#	sudo gatttool -b $ID --char-write-req -a 0x34 -n 00 > useless.txt #disables (0x44)
#
#	# Manipulating data
#	outputPrefix="Characteristic value/descriptor: "
#	raw_info_data=${infoOutput#$outputPrefix} #Removes prefix of luxOutput
#	info="$(python conversion_func.py info "${raw_info_data}")" # Converts raw_bar_data to celsius
#	IFS='|' read -ra ADDR <<< "$info"
#
#        perf=${ADDR[0]}
#        batt=${ADDR[1]}
#        PIR=${ADDR[2]}
#        reed=${ADDR[3]}
#	light=${ADDR[4]}
#        info=${ADDR[5]}
#}

reqbar(){
        #echo "Reading " $Name
        sudo gatttool -b $ID --char-write-req -a 0x34 -n 01 > /dev/null 2>&1 #initiates (0x44)
        sleep 1.1
        barOutput="$(sudo gatttool -b $ID --char-read -a 0x31)" #collects 0x41)
        sleep 0.1
        sudo gatttool -b $ID --char-write-req -a 0x34 -n 00 > /dev/null 2>&1 #disables (0x44)

        # Manipulating data
        outputPrefix="Characteristic value/descriptor: "
        raw_bar_data=${barOutput#$outputPrefix} #Removes prefix of luxOutput
        bar="$(python conversion_func.py bar "${raw_bar_data}")" # Converts raw_bar_data to celsius
        
        IFS='|' read -ra ADDR <<< "$bar"

        temp_bar_sens=${ADDR[0]}
        bar_bar_sens=${ADDR[1]}
}


reqmov(){
#        sudo gatttool -b $Sensor --char-write-req -a 0x3C -n 3F00 #initiates (0x44)
#        movOutput="$(sudo gatttool -b $Sensor --char-read -a 0x39)" #collects 0x41)
#        sudo gatttool -b $Sensor --char-write-req -a 0x34 -n 00 #disables (0x44)
	echo "mov"
}

Occupancy()
{
        echo "1" > wait.txt
        #reqtemp
	#reqinfo
	if [ $Action_3 == "1" ]; then
		reqhum
		reqbar
	fi
        reqtemp

	#Write Data
    	dt=$(date '+%m/%d/%y %H:%M:%S');

    	echo "${dt}|${log}|${temp_hum_sens}|${hum_hum_sens}|${perf}|${batt}|${PIR}|${reed}|${light}|${info}|${temp_bar_sens}|${bar_bar_sens}|${raw_hum_data}|${raw_temp_data}|${raw_bar_data}|${Action_1}|${Action_2}|${Action_3}|" # pr
        printf "\n${dt}|${log}|${temp_hum_sens}|${hum_hum_sens}|${perf}|${batt}|${PIR}|${reed}|${light}|${info}|${temp_bar_sens}|${bar_bar_sens}|${raw_hum_data}|${raw_temp_data}|${raw_bar_data}|${Action_1}|${Action_2}|${Action_3}|" >> $File #prints $

        echo "2" > wait.txt
	#		sleep 10
}

Name=$1
ID=$2
File=$3
Action_1=$4
log=$7
Action_2=$5
Action_3=$6
#echo $Name
#echo "Detector"
Occupancy
#echo "Over"
exit

#        echo "Resetting..."
#        sudo hciconfig hci0 reset #reset the adapter
#        sleep 8
#done

#or reset the BLuethoot with: sudo /etc/init.d/bluetooth restartReset the adapter: sudo hciconfig hci0 reset or reset the BLuethoot with:
#sudo /etc/init.d/bluetooth restart
