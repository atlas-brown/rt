#!/bin/sh

# look in DIR for *.sh files and create symbolic links to the ones
# that match any of the given tags

# fetch_scripts_by_tag [OPTIONS] TAG... DIR
# TAG...: the tags to look for
# DIR: the directory to look for files in
# OPTIONS:
#     -s:       swap order of args ('[OPTIONS] DIR TAG...')
#     -r:       look in subdirectories
#     -a:       only fetch files that match all tags
#     -e <tag>: exclude scripts containing the given tag (use multiple times to exclude multiple tags)
#     -o <dir>: name of the output folder (default "script_symlinks/")
#     -v:       verbose output (announce created symlinks)

# default values
dir_first=false
recursive=false
match_all=false
output_dir="script_symlinks"
excluded_tags=""
verbose=false

# parse options using getopts
while getopts "srao:e:v" opt; do
    case $opt in
        s)
            dir_first=true
            ;;
        r)
            recursive=true
            ;;
        a)
            match_all=true
            ;;
        o)
            output_dir=${OPTARG%/} # remove trailing slash
            output_dir=${output_dir#./} # remove leading dot-slash
            ;;
        e)
            excluded_tags="$excluded_tags $OPTARG"
            ;;
        v)
            verbose=true
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            exit 1
            ;;
        \?) ;; # getopts will take care of unknown flags
    esac
done
shift $((OPTIND - 1))

# check for required arguments
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 [OPTIONS] TAG... DIR" >&2
    exit 1
fi

if [ "$dir_first" = false ]; then
    # [OPTIONS] TAG... DIR

    # remove the last argument
    i=0; len="$#"
    for arg; do
        i=$((i + 1))
        if [ $i = 1 ]; then set --; fi # set args to empty on first loop
        if [ $i = $len ]; then break; fi # break before adding the last arg
        set -- "$@" "$arg" # add the current arg
    done

    search_dir="${arg%/}" # remove trailing slash
    search_dir="${search_dir#./}" # remove leading dot-slash
else
    # [OPTIONS] DIR TAG...

    arg="$1"
    shift # remove $1 from the args array
fi

search_dir="${arg%/}" # remove trailing slash
search_dir="${search_dir#./}" # remove leading dot-slash

# create output directory if it doesn't exist
mkdir -p "$output_dir"

# find shell script files
if [ "$recursive" = true ]; then
    find_cmd="find \"$search_dir\" -type f -name '*.sh'"
else
    # POSIX-compliant way to implement -maxdepth
    find_cmd="find \"$search_dir\"/. ! -name . -prune -type f -name '*.sh'"
fi

# process each file
# shellcheck disable=SC2086
eval $find_cmd | while IFS= read -r filename; do
    filename=${filename#./} # remove leading dot-slash

    # find the tags in the file
    tags_line=$(sed -n 's/^# tags: //p' "$filename")
    [ -z "$tags_line" ] && continue

    all_matched=true
    none_matched=true
    for tag in $(echo "$tags_line" | tr ',' ' '); do
        # if any tag of the file is excluded, move on to the next file
        for excluded_tag in $excluded_tags; do
            if [ "$tag" = "$excluded_tag" ]; then
                continue 3
            fi
        done

        for search_tag; do
            if [ "$search_tag" = "$tag" ]; then
                # at least one tag matched
                none_matched=false
            else
                # at least one tag did not match
                all_matched=false
            fi
        done
    done

    if [ "$none_matched" = true ]; then
        continue
    fi

    if [ "$match_all" = true ] && ! $all_matched; then
        continue
    fi

    # changes 'some/directory' to '../..'
    reverse_output_dir=$(echo "$output_dir" | sed "s|[^\/][^\/]*|\.\.|g")
    ln -fs "$reverse_output_dir/$filename" "$output_dir"

    if [ "$verbose" = true ]; then
        printf "Created soft link: '%s' in '%s'\n" \
            "$reverse_output_dir/$filename" \
            "$output_dir/"
    fi
done
