#!/bin/bash

shopt -s nocasematch

SOURCE="${BASH_SOURCE[0]}"
# resolve $SOURCE until the file is no longer a symlink
while [ -h "$SOURCE" ]; do
	DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
	SOURCE="$(readlink "$SOURCE")"
	[[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR="$(dirname "${SOURCE}")"

path="${1}"

parsepath() {
	dir="$(/usr/bin/dirname "${1}")"
	name_no_ext="$(/usr/bin/basename "${1}" | /usr/bin/cut -f 1 -d '.')"
	printf "%s\n" "${dir}/${name_no_ext}"
}

case "${path}" in
*".zip")
	target="$(parsepath "${path}")"
	mkdir -p "${target}"
	/usr/bin/ditto -xk "${path}" "${target}"
	/bin/mv -f "${path}" ~/.Trash/
	;;
*".tgz"|*".gz")
	/usr/bin/tar -xvf "${path}" -C ~/Downloads
	/bin/mv -f "${path}" ~/.Trash/
	;;
*".dmg")
	mounted_path=$(/usr/bin/yes | /usr/bin/hdiutil attach -nobrowse "${path}" | /usr/bin/tail -n 1 | /usr/bin/grep -E -o "/Volumes/.+$")
	/bin/cp -R "${mounted_path}" ~/Downloads
	/usr/bin/hdiutil detach "${mounted_path}" 1>/dev/null
	/bin/mv -f "${path}" ~/.Trash/
	;;
*".heic")
	/usr/bin/sips -s format jpeg "${path}" --out "$(parsepath "${path}").jpg"
	/bin/mv -f "${path}" ~/.Trash/
esac
