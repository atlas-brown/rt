#!/bin/bash

servers="testing-kafka-dev01:9092,testing-kafka-dev02:9092,testing-kafka-dev03:9092"
topic="test"

declare -A pairs=( [512000]=1024 [4096000]=128 [51200]=10240 [500]=1048576 )

echo "records,size,acks,compression,inflight,batch,linger,time,batch-size-avg,batch-size-max,batch-split-rate,batch-split-total,buffer-available-bytes,buffer-exhausted-rate,buffer-exhausted-total,buffer-total-bytes,bufferpool-wait-ratio,bufferpool-wait-time-total,compression-rate-avg,connection-close-rate,connection-close-total,connection-count,connection-creation-rate,connection-creation-total,failed-authentication-rate,failed-authentication-total,failed-reauthentication-rate,failed-reauthentication-total,incoming-byte-rate,incoming-byte-total,io-ratio,io-time-ns-avg,io-wait-ratio,io-wait-time-ns-avg,io-waittime-total,iotime-total,metadata-age,network-io-rate,network-io-total,outgoing-byte-rate,outgoing-byte-total,produce-throttle-time-avg,produce-throttle-time-max,reauthentication-latency-avg,reauthentication-latency-max,record-error-rate,record-error-total,record-queue-time-avg,record-queue-time-max,record-retry-rate,record-retry-total,record-send-rate,record-send-total,record-size-avg,record-size-max,records-per-request-avg,request-latency-avg,request-latency-max,request-rate,request-size-avg,request-size-max,request-total,requests-in-flight,response-rate,response-total,select-rate,select-total,successful-authentication-no-reauth-total,successful-authentication-rate,successful-authentication-total,successful-reauthentication-rate,successful-reauthentication-total,waiting-threads,incoming-byte-rate--2,incoming-byte-rate-1,incoming-byte-rate-2,incoming-byte-rate-3,incoming-byte-total--2,incoming-byte-total-1,incoming-byte-total-2,incoming-byte-total-3,outgoing-byte-rate--2,outgoing-byte-rate-1,outgoing-byte-rate-2,outgoing-byte-rate-3,outgoing-byte-total--2,outgoing-byte-total-1,outgoing-byte-total-2,outgoing-byte-total-3,request-latency-avg--2,request-latency-avg-1,request-latency-avg-2,request-latency-avg-3,request-latency-max--2,request-latency-max-1,request-latency-max-2,request-latency-max-3,request-rate--2,request-rate-1,request-rate-2,request-rate-3,request-size-avg--2,request-size-avg-1,request-size-avg-2,request-size-avg-3,request-size-max--2,request-size-max-1,request-size-max-2,request-size-max-3,request-total--2,request-total-1,request-total-2,request-total-3,response-rate--2,response-rate-1,response-rate-2,response-rate-3,response-total--2,response-total-1,response-total-2,response-total-3,byte-rate,byte-total,compression-rate,record-error-rate,record-error-total,record-retry-rate,record-retry-total,record-send-rate,record-send-total"

for records in "${!pairs[@]}"; do
    for acks in -1 0 1; do
        for compression in "snappy" "none"; do
            for inflight in 1 5 10; do
                for batch in 0 1048576 9437184; do
                    for linger in 0 20 1000; do
                        start=$(date +%s)
                        metrics=$(kafka-producer-perf-test --topic ${topic} --num-records ${records} --record-size ${pairs[$records]} --throughput -1 --print-metrics --producer-props bootstrap.servers=${servers} client.id=test acks=${acks} compression.type=${compression} max.in.flight.requests.per.connection=${inflight} batch.size=${batch} linger.ms=${linger}) 
                        time=$(($(date +%s) - ${start}))
                        
                        echo -n "$records,${pairs[$records]},$acks,\"$compression\",$inflight,$batch,$linger,$time"

                        while IFS= read -r metric; do 
                            regex='producer-metrics:(.*):\{.*\}\s+: (.*)'
                            if [[ "${metric}" =~ $regex ]]; then
                                echo -n ",${BASH_REMATCH[2]}"
                            fi
                            regex='producer-node-metrics:(.*):\{.*node-id=node-(.*)\}\s+: (.*)'
                            if [[ "${metric}" =~ $regex ]]; then
                                echo -n ",${BASH_REMATCH[3]}"
                            fi
                            regex='producer-topic-metrics:(.*):\{.*\}\s+: (.*)'
                            if [[ "${metric}" =~ $regex ]]; then
                                echo -n ",${BASH_REMATCH[2]}"
                            fi
                        done <<< "$metrics"
                        echo

                    done
                done
            done
        done
    done
done