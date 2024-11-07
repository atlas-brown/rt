
#!/bin/sh

usage() {
    echo "Usage: $0 [-l length] [-s] [-n] [-u]" 1>&2
    exit 1
}

length=8
special=false
numbers=false
uppercase=false

while getopts "l:snu" o; do
    case "${o}" in
        l)
            length=${OPTARG}
            ;;
        s)
            special=true
            ;;
        n)
            numbers=true
            ;;
        u)
            uppercase=true
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ "$special" = true ]; then
    characters+="!@#$%^&*()_+"
fi
if [ "$numbers" = true ]; then
    characters+="0123456789"
fi
if [ "$uppercase" = true ]; then
    characters+="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
fi
characters+="abcdefghijklmnopqrstuvwxyz"

password=$(cat /dev/urandom | tr -dc "$characters" | head -c $length | shuf)

echo "Generated password: $password"
