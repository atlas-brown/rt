#!/bin/sh

# Samsung Camera
echo "Samsung Camera Tunnels:"
ssh -f -p 2324 giggle.enhancedreality.net -L 8081:127.0.0.1:8081 -N
echo "Started Tunnel for mjpeg stream as PID $!"
ssh -f -p 2324 giggle.enhancedreality.net -L 9102:172.16.10.33:80 -N
echo "Started Tunnel for camera computer as PID $!"

