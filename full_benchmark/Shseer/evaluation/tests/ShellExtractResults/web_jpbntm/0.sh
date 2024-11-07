#!/bin/sh

# Samsung Camera
echo "PTZOptics Tunnels:"
echo "Starting Tunnel for mjpeg stream..."
ssh -f -p 2326 giggle.enhancedreality.net -L 8081:127.0.0.1:8081 -N
echo "Starting Tunnel for camera computer"
ssh -f -p 2326 giggle.enhancedreality.net -L 9102:172.16.10.33:80 -N

