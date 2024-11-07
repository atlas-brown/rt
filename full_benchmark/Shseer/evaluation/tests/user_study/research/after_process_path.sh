#!/bin/bash

shopt -s nocasematch

SOURCE="${BASH_SOURCE[0]}"
# resolve $SOURCE until the file is no longer a symlink
while [ -h "$SOURCE" ]; do
	DIR="$(/usr/bin/cd -P "$(/usr/bin/dirname "$SOURCE")" >/dev/null 2>&1 && /bin/pwd)"
	SOURCE="$(/usr/bin/readlink "$SOURCE")"
	[[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR="$(/usr/bin/dirname "${SOURCE}")"

path="${1}"
parsepath() {
	dir="$(/usr/bin/dirname "${1}")"
	name_no_ext="$(/usr/bin/basename "${1}" | /usr/bin/cut -f 1 -d '.')"
	/usr/bin/printf "%s\n" "${dir}/${name_no_ext}"
}

output=""
case "${path}" in
*".zip")
	target="$(parsepath "${path}")"
	mkdir -p "${target}"
	/usr/bin/ditto -xk "${path}" "${target}"
	output="${target}"
	/bin/mv -f "${path}" ~/.Trash/
	;;
*".tgz"|*".gz")
	tar_output=$(/usr/bin/tar -xvf "${path}" -C ~/Downloads)
	output=$(printf "%s\n" "${tar_output}" | sed 's/x //' | sed -E '/^\.\//d' | sed -E "s|^|${HOME}/Downloads/|")
	/bin/mv -f "${path}" ~/.Trash/
	;;
*".dmg")
	mounted_path=$(/usr/bin/yes | /usr/bin/hdiutil attach -nobrowse "${path}" | /usr/bin/tail -n 1 | /usr/bin/grep -E -o "/Volumes/.+$")
	/bin/cp -R "${mounted_path}" ~/Downloads
	output=~/Downloads/$(basename "${mounted_path}")
	/usr/bin/hdiutil detach "${mounted_path}" 1>/dev/null
	/bin/mv -f "${path}" ~/.Trash/
	;;
*".heic")
	output="$(parsepath "${path}").jpg"
	/usr/bin/sips -s format jpeg "${path}" --out "${output}"
	/bin/mv -f "${path}" ~/.Trash/
	;;
*)
	output="${path}"
	;;
esac
/usr/bin/printf "%s" "${output}"
