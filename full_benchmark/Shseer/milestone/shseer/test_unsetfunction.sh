#!/bin/sh
Func () {
	echo "Hello world!"
}

unset -f Func
#Func is unset
Func