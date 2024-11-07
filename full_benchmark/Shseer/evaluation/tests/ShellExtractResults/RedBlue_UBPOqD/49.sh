##############################################################################
# rbe.sh to run the RBE from TPC-W Java Implementation.
# 2003 by Jan Kiefer.
#
# This file is distributed "as is". It comes with no warranty and the 
# author takes no responsibility for the consequences of its use.
#
# Usage, distribution and modification is allowed to everyone, as long 
# as reference to the author is given and this license note is included.
##############################################################################

#!/bin/sh

# $1 = run nr
# $2 = nr of ebs (rbe)

help()
{
  cat <<HELP
rbe.sh - start rbe for tpc-w
usage: rbe [option]
where option can be:

    -r <nr>
	set the number of the run (for filename only), default: 1

    -n <nr>
	set the nummber of ebs to start, default: 20

    -u <seconds>
	ramp up time, default: 100

    -i <seconds>
	measurement interval time, default: 1200

    -d <seconds>
	ramp down time, default: 50

    -w <url>
	url of SUT to use, default: http://tiamak/tpcw/

    -t <nr>
	set the type for the rbe to use
		1: Browsing Mix
		2: Shopping mix (default)
		3: Ordering Mix

HELP
  exit 0
}

error()
{
    # print an error and exit
    echo "$1"
    exit 1
}

tftype=2
runnr=1
numebs=@num.eb@
numitem=@num.item@
ru=50
mi=300
rd=10
url="@standardUrl@@tpcwUrlPath@/"
CUSTOMERS=`echo "2880*$numebs" | bc`
backend=""
dc="0"
uid="0"

# The option parser, change it as needed
# In this example -f and -h take no arguments -l takes an argument
# after the l
while [ -n "$1" ]; do
case $1 in
    -h) help;shift 1;; # function help is called
    -r) runnr=$2;shift 2;;
    -n) numebs=$2;shift 2;;
    -u) ru=$2;shift 2;;
    -i) mi=$2;shift 2;;
    -d) rd=$2;shift 2;;
    -w) url=$2;shift 2;;
    -t) tftype=$2;shift 2;;
    -b) backend=$2;shift 2;;
    -l) dc=$2;shift 2;;
    -m) uid=$2;shift 2;;
    
    --) shift;break;; # end of options
    -*) echo "error: no such option $1. -h for help";exit 1;;
    *)  break;;
esac
done
mkdir -p results
MIX=""
if [ $tftype -eq 1 ]
	then	MIX="Browsing"
elif [ $tftype -eq 2 ]
	then	MIX="Shopping"
elif [ $tftype -eq 3 ]
	then	MIX="Ordering"
fi

datum=`date +%d_%H%M%S`
fact="rbe.EBTPCW"$tftype"Factory"
filename="results/"$MIX"_"$backend"_dcid"$dc"_uid"$uid"_e"$numebs"_t"$mi"_"$datum".m"
outputfilename=$filename".output"
error=`echo "($mi/60)*10*$numebs" | bc`
#java rbe.RBE -EB $fact $numebs -OUT $filename -RU $ru -MI $mi -RD $rd -WWW $url -ITEM $numitem -CUST $CUSTOMERS -GETIM true -MAXERROR $error -TT 1.0 &> | tee $outputfilename
java rbe.RBE -EB $fact $numebs -OUT $filename -RU $ru -MI $mi -RD $rd -WWW $url -ITEM $numitem -CUST $CUSTOMERS -GETIM true -MAXERROR $error -TT @thinktime@ &>  $outputfilename
#java rbe.RBE -EB $fact $numebs I__BBBCHNOOPSSS -OUT $filename -RU $ru -MI $mi -RD $rd -WWW $url -ITEM $numitem -CUST $CUSTOMERS -GETIM true -MAXERROR $error -TT @thinktime@ &>  $outputfilename
echo "command:"
echo ""
echo ""
echo "java rbe.RBE -EB $fact $numebs -OUT $filename -RU $ru -MI $mi -RD $rd -WWW $url -ITEM $numitem -CUST $CUSTOMERS -GETIM true -MAXERROR $error -TT @thinktime@ &>  $outputfilename"

echo ""
echo ""
