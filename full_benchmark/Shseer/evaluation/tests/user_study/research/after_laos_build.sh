#!/bin/bash

dev=$1
rev=$2
thr=$3

if [ "${thr}" == "" ]; then
    dthr=$(nproc --all)
else
    dthr="${thr}"
fi

### FUNCTIONS ###

function update_repo {
    cd "${HOME}/android/laos_${rev}/.repo/repo" || exit
    echo
    git pull
    DIFF=$(diff repo "${HOME}/bin/repo")
    if [ "${DIFF}" != "" ]; then
        echo
        diff repo "${HOME}/bin/repo"
        echo
        cp -vi repo "${HOME}/bin/repo"
    else
        echo
        echo "repo unmodified"
    fi
}

function local_security_patch_level {
    echo "The current security patch level for laos ${rev} is..."
    grep "PLATFORM_SECURITY_PATCH := " build/core/version_defaults.mk
}

function remote_security_patch_level {
    if [ "${rev}" == "14.1" ]; then
        url="https://raw.githubusercontent.com/LineageOS/android_build/cm-14.1/core/version_defaults.mk"
    else
        url="https://raw.githubusercontent.com/LineageOS/android_build/lineage-${rev}/core/version_defaults.mk"
    fi
    echo "The current remote security patch level for laos ${rev} is..."
    wget -q "${url}" -O - | grep "PLATFORM_SECURITY_PATCH := "
}

function compare_security_patch_level {
    local_security_patch_level || exit
    echo
    remote_security_patch_level || exit
}

function clean_repository {
    while true; do
        read -p "Do you wish to clean the repository? Type A/a for agressive or Y/y for normal or N/n and hit return: " ayn
        case $ayn in
            [Aa]* ) echo;
                    repo forall -c git gc --aggressive --prune=now && repo forall -c git repack -Ad && repo forall -c git prune;
                    break;;
            [Yy]* ) echo;
                    repo forall -c git gc --prune=now && repo forall -c git repack -Ad && repo forall -c git prune;
                    break;;
            [Nn]* ) break;;
        esac
    done
}

function pick_unmerged_commits {
    echo "Picking unmerged commits"
    if [ "${rev}" == "14.1" ]; then
        echo
        #2020-04-05
        for com in 272352 272353 272354 272355 272356 ; do
            repopick ${com} 2>&1
        done
    fi
    if [ "${rev}" == "15.1" ]; then
        echo
        #2020-04-05
        for com in 272393 272394 272395 272396 272397 272663 272816 ; do
            repopick ${com} 2>&1
        done
    fi
    if [ "${rev}" == "16.0" ]; then
        echo
        #2020-05-05
        for com in 275014 275015 275016 275017 275019 275020 275021 275022 275023 275024 275025 275026 275027 275028 275029 275030 275031 275194 ; do
            repopick ${com} 2>&1
        done
    fi
    if [ "${rev}" == "17.1" ]; then
        echo
        #soong: java: Specify larger heap size for metalava
        repopick -f 266411 2>&1
    fi
}

function sync_repository {
    while true; do
        read -p "Do you wish to sync the repository? Type Y/y or N/n and hit return: " yn
        case $yn in
            [Yy]* ) echo
                    if [ "${dev}" == "potter" ] || [ "${dev}" == "thea" ]; then
                        rm -rfv ./device/motorola ./kernel/motorola ./vendor/motorola
                    elif [ "${dev}" == "sargo" ]; then
                        rm -rfv ./device/google ./kernel/google ./vendor/google
                    fi
                    echo
                    repo sync -v -j "${dthr}" -c --no-tags --no-clone-bundle --force-sync 2>&1
                    echo
                    local_security_patch_level || exit
                    echo
                    clean_repository || exit
                    echo
                    export LC_ALL=C
                    source build/envsetup.sh
                    echo
                    pick_unmerged_commits || exit
                    echo
                    local_security_patch_level || exit
                    break;;
            [Nn]* ) break;;
        esac
    done
}

function build {
    breakfast "${dev}"
    croot
    if [ "${thr}" == "" ]; then
        brunch "${dev}"
    else
        breakfast "${dev}"
        make bacon -j "${thr}"
    fi
    cd "${OUT}" || exit
}

function cleanup {
    if [ "$rev" == "14.1" ] || [ "$rev" == "15.1" ]; then
        rm -rfv "./obj/PACKAGING/target_files_intermediates/lineage_${dev}-target_files-"*
    fi
    rm -fv ./system/build.prop
    rm -fv ./obj/ETC/system_build_prop_intermediates/build.prop
    rm -fv "./lineage_${dev}-ota-"*.zip
    rm -fv "./lineage-${rev}-"*"-UNOFFICIAL-${dev}.zip.md5sum"
    output="$(ls "lineage-${rev}-"*"-UNOFFICIAL-${dev}.zip")"
    outputtag=""
    if [ "${rev}" == "17.1" ]; then
        outputtag="TEST-"
    fi
    mv -v "${output}" "${HOME}/Schreibtisch/${outputtag}${output}"
    pkill java
    echo
    while true; do
        read -p "Do you wish to clean the out-directory? Type Y/y or N/n and hit return: " yn
        case $yn in
            [Yy]* ) echo
                    rm -rfv "${HOME}/android/laos_${rev}/out"
                    break;;
            [Nn]* ) break;;
        esac
    done
}

### START ###

update_repo || exit
cd "${HOME}/android/laos_${rev}" || exit
echo
compare_security_patch_level || exit
echo
sync_repository || exit
echo
while true; do
    read -p "Do you wish to build clean? Type Y/y or N/n or A/a to abort and hit return: " yna
    case $yna in
        [Yy]* ) echo
                rm -rfv ./out
                break;;
        [Nn]* ) break;;
        [Aa]* ) exit;;
    esac
done
echo
build || exit
echo
echo "Press ENTER to continue..."
echo
read -s
cleanup || exit
exit
