#!/bin/bash

function query_device_id {
    xinput list | grep -i touchpad | sed 's/.*id=\([0-9]*\).*/\1/g'
}

let device_id=$(query_device_id)

let state=$(xinput list-props $device_id | grep Enabled | awk '{print $4;}')

let new_state=$((1 - $state))

xinput set-prop $device_id "Device Enabled" $new_state
