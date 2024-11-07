#!/bin/bash

servers="testing-kafka-dev01:9092,testing-kafka-dev02:9092,testing-kafka-dev03:9092"
topic="test"

declare -A pairs=( [512000]=1024 [4096000]=128 )
#declare -A pairs=( [100]=1024 )

#echo "records,size,acks,compression,inflight,batch,linger,time,batch-size-avg,batch-size-max,batch-split-rate,batch-split-total,buffer-available-bytes,buffer-exhausted-rate,buffer-exhausted-total,buffer-total-bytes,bufferpool-wait-ratio,bufferpool-wait-time-total,compression-rate-avg,connection-close-rate,connection-close-total,connection-count,connection-creation-rate,connection-creation-total,failed-authentication-rate,failed-authentication-total,failed-reauthentication-rate,failed-reauthentication-total,incoming-byte-rate,incoming-byte-total,io-ratio,io-time-ns-avg,io-wait-ratio,io-wait-time-ns-avg,io-waittime-total,iotime-total,metadata-age,network-io-rate,network-io-total,outgoing-byte-rate,outgoing-byte-total,produce-throttle-time-avg,produce-throttle-time-max,reauthentication-latency-avg,reauthentication-latency-max,record-error-rate,record-error-total,record-queue-time-avg,record-queue-time-max,record-retry-rate,record-retry-total,record-send-rate,record-send-total,record-size-avg,record-size-max,records-per-request-avg,request-latency-avg,request-latency-max,request-rate,request-size-avg,request-size-max,request-total,requests-in-flight,response-rate,response-total,select-rate,select-total,successful-authentication-no-reauth-total,successful-authentication-rate,successful-authentication-total,successful-reauthentication-rate,successful-reauthentication-total,waiting-threads,node-incoming-byte-rate--3,node-incoming-byte-rate-1,node-incoming-byte-rate-2,node-incoming-byte-rate-3,node-incoming-byte-total--3,node-incoming-byte-total-1,node-incoming-byte-total-2,node-incoming-byte-total-3,node-outgoing-byte-rate--3,node-outgoing-byte-rate-1,node-outgoing-byte-rate-2,node-outgoing-byte-rate-3,node-outgoing-byte-total--3,node-outgoing-byte-total-1,node-outgoing-byte-total-2,node-outgoing-byte-total-3,node-request-latency-avg--3,node-request-latency-avg-1,node-request-latency-avg-2,node-request-latency-avg-3,node-request-latency-max--3,node-request-latency-max-1,node-request-latency-max-2,node-request-latency-max-3,node-request-rate--3,node-request-rate-1,node-request-rate-2,node-request-rate-3,node-request-size-avg--3,node-request-size-avg-1,node-request-size-avg-2,node-request-size-avg-3,node-request-size-max--3,node-request-size-max-1,node-request-size-max-2,node-request-size-max-3,node-request-total--3,node-request-total-1,node-request-total-2,node-request-total-3,node-response-rate--3,node-response-rate-1,node-response-rate-2,node-response-rate-3,node-response-total--3,node-response-total-1,node-response-total-2,node-response-total-3,topic-byte-rate,topic-byte-total,topic-compression-rate,topic-record-error-rate,topic-record-error-total,topic-record-retry-rate,topic-record-retry-total,topic-record-send-rate,topic-record-send-total"

for records in "${!pairs[@]}"; do
    for acks in -1 0 1; do
        for compression in "snappy" "none"; do
            for inflight in 1 5 10; do
                for batch in 0; do
                    for linger in 0 20 150 1000; do
                        ncout="$(nc -zv testing-kafka-dev01 9092 2>&1 && nc -zv testing-kafka-dev02 9092 2>&1 && nc -zv testing-kafka-dev03 9092 2>&1)"
                        if [[ $? != 0 ]]; then
                            echo "$records,${pairs[$records]},$acks,\"$compression\",$inflight,$batch,$linger,BROKER BROKEN: ${ncout}"
                            echo
                            continue
                        fi

                        (kafka-leader-election --bootstrap-server testing-kafka-dev01:9092,testing-kafka-dev02:9092,testing-kafka-dev03:9092 --election-type preferred --all-topic-partitions)
                        
                        start=$(date +%s%3N)

                        metrics="$(kafka-producer-perf-test --topic ${topic} --num-records ${records} --record-size ${pairs[$records]} --throughput -1 --print-metrics --producer-props bootstrap.servers=${servers} client.id=test acks=${acks} compression.type=${compression} max.in.flight.requests.per.connection=${inflight} batch.size=${batch} linger.ms=${linger})"
                        if [[ $? == 124 ]]; then
                            echo "$records,${pairs[$records]},$acks,\"$compression\",$inflight,$batch,$linger,TIMEOUT"
                            echo
                            continue
                        fi

                        time=$(($(date +%s%3N) - ${start}))
                        
                        echo "$records,${pairs[$records]},$acks,\"$compression\",$inflight,$batch,$linger,$time"
                        #echo "$metrics"

                        while IFS= read -r metric; do 
                            regex="${records} records sent.*"
                            if [[ "${metric}" =~ $regex ]]; then
                                echo "$metric"
                            fi
                            regex='producer-metrics:(.*):\{.*\}\s+: (.*)'
                            if [[ "${metric}" =~ $regex ]]; then
                                echo "$metric"
                                #echo -n ",${BASH_REMATCH[2]}"
                                #echo -n ",${BASH_REMATCH[1]}"
                            fi
                            regex='producer-node-metrics:(.*):\{.*node-id=node-(.*)\}\s+: (.*)'
                            if [[ "${metric}" =~ $regex ]]; then
                                echo "$metric"
                                #echo -n ",${BASH_REMATCH[3]}"
                                #echo -n ",node-${BASH_REMATCH[1]}-${BASH_REMATCH[2]}"
                            fi
                            regex='producer-topic-metrics:(.*):\{.*\}\s+: (.*)'
                            if [[ "${metric}" =~ $regex ]]; then
                                echo "$metric"
                                #echo -n ",${BASH_REMATCH[2]}"
                                #echo -n ",topic-${BASH_REMATCH[1]}"
                            fi
                        done <<< "$metrics"

                        sleep 3
                    done
                done
            done
        done
    done
done