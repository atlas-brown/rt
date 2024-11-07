#!/bin/bash

# For the test, we shall use 4 subscribers and 4 publishers, grouped by 2 in different brokers, all of which will will be subscribed/publish at the same topic. More precisely, we will subscribe 2 clients in broker 1 and 2 other clients in broker 2. In addition, other 4 publish-clients will publish 2 in broker 3 and 2 in broker 4. Broker 5 doesn't have any client.


# Subscriber ip assignement:
# sub_1 -> 172.20.0.21 -> subscribed hivemq 172.20.0.2
# sub_2 -> 172.20.0.22 -> subscribed hivemq 172.20.0.2
# sub_3 -> 172.20.0.31 -> subscribed hivemq 172.20.0.3
# sub_4 -> 172.20.0.32 -> subscribed hivemq 172.20.0.3

# For simplicity, we do not add more than 9 clients to a broker
IP_ADDR="172.20.0."
NETWORK_NAME="pumba_net"
CLUSTER_TYPE="vernemq"
# must be even number of clients for sake of simplicity
TOTAL_SUBSCRIBERS=4
NR_SUBSCRIBERS_PER_BROKER=2
NR_BROKERS=$((TOTAL_SUBSCRIBERS/NR_SUBSCRIBERS_PER_BROKER))


PWD=$(pwd)
FIST_BROKER_NUM=2
LAST_BROKER_NUM=$((FIST_BROKER_NUM + NR_BROKERS-1))

# For the publishers we can also make them run in the FOREGROUND to log their debug, as they are temporary and after they kill themself automatically
# This strategy doesn't work with subscribers, since they remain active, so what can be done in that case is to fetch the debug stream after we have finished running the network, just before killing the running processes.

for broker in $(seq $FIST_BROKER_NUM $LAST_BROKER_NUM)
	do
		for sub in $(seq 1 $NR_SUBSCRIBERS_PER_BROKER)
			do
				echo "Subscriber $IP_ADDR$broker$sub subscribing to broker $IP_ADDR$broker"
				docker run -d --rm -it --network=$NETWORK_NAME \
						--ip="$IP_ADDR$broker$sub" \
						--name="sub_$broker$sub" \
						piersfinlayson/mosquitto-clients mosquitto_sub \
						-h "$IP_ADDR$broker"  \
						-t test \
						-d | xargs -d$'\n' -L1 echo ""
				# Sleeping 5 seconds to permit all message exchange occur
				sleep 5
			done
	done

#docker run --rm -ti --network=$NETWORK_NAME \
#						--ip="$IP_ADDR$broker$sub" \
#						--name="sub_$broker$sub" \
#						piersfinlayson/mosquitto-clients mosquitto_sub \
#						-h "$IP_ADDR$broker"  \
#						-t test  \
#						-d | xargs -d$'\n' -L1 bash -c 'date "+%Y-%m-%d %T.%3N ---- $0"' \
#						| xargs -d$'\n' -L1 echo "$IP_ADDR$broker$sub -" >> "../Network Analysis/hivemq_log$broker$sub.log" &


