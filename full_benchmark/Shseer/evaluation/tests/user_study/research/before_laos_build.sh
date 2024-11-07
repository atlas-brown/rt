#!/bin/bash

dev=$1
rev=$2
thr=$3

if [ "${thr}" == "" ]; then
      dthr=$(nproc --all)
else
      dthr="${thr}"
fi

cd "${HOME}/android/laos_${rev}/.repo/repo" || exit
git pull
DIFF=$(diff repo "${HOME}/bin/repo")
if [ "${DIFF}" != "" ]; then
    echo ""
    diff repo "${HOME}/bin/repo"
    echo ""
    cp -vi repo "${HOME}/bin/repo"
else
    echo "repo unmodified"
fi
cd "${HOME}/android/laos_${rev}" || exit
echo
echo "The current security patch level for laos ${rev} is..."
grep "PLATFORM_SECURITY_PATCH := " build/core/version_defaults.mk
echo
if [ "${rev}" == "14.1" ]; then
    url="https://raw.githubusercontent.com/LineageOS/android_build/cm-14.1/core/version_defaults.mk"
else
    url="https://raw.githubusercontent.com/LineageOS/android_build/lineage-${rev}/core/version_defaults.mk"
fi
echo "The current remote security patch level for laos ${rev} is..."
wget -q "${url}" -O - | grep "PLATFORM_SECURITY_PATCH := "
echo
while true; do
    read -p "Do you wish to sync the repository? Type Y/y or N/n and hit return: " yn
    case $yn in
        [Yy]* ) echo; \
                if [ "${dev}" == "potter" ] || [ "${dev}" == "thea" ]; then
                      rm -rfv ./device/motorola ./kernel/motorola ./vendor/motorola
                elif [ "${dev}" == "sargo" ]; then
                      rm -rfv ./device/google ./kernel/google ./vendor/google
                fi; \
                echo; \
                repo sync -v -j "${dthr}" -c --no-tags --no-clone-bundle --force-sync 2>&1; break;;
        [Nn]* ) break;;
    esac
done
echo
echo "The current security patch level for laos ${rev} is..."
grep "PLATFORM_SECURITY_PATCH := " build/core/version_defaults.mk
echo
while true; do
    read -p "Do you wish to clean the repository? Type A/a for agressive or Y/y for normal or N/n and hit return: " ayn
    case $ayn in
        [Aa]* ) echo; repo forall -c git gc --aggressive --prune=now && repo forall -c git repack -Ad && repo forall -c git prune; break;;
        [Yy]* ) echo; repo forall -c git gc --prune=now && repo forall -c git repack -Ad && repo forall -c git prune; break;;
        [Nn]* ) break;;
    esac
done
echo
export LC_ALL=C
source build/envsetup.sh
echo
echo "Picking unmerged commits"
echo
if [ "${rev}" == "14.1" ]; then
      echo
      #2020-03-05
      for com in 270196 270217 270218 270219 270220 270221 270222 270223 ; do
              repopick ${com} 2>&1
      done
      #2020-04-05
      for com in 272352 272353 272354 272355 272356 ; do
              repopick ${com} 2>&1
      done
      echo
fi
if [ "${rev}" == "15.1" ]; then
      echo
      #2020-03-05
      for com in 270122 270123 270124 270125 270126 270127 270128 270129 270130 270290 ; do
              repopick ${com} 2>&1
      done
      #2020-04-05
      for com in 272393 272394 272395 272396 272397 272663 272816 ; do
              repopick ${com} 2>&1
      done
      echo
fi
if [ "${rev}" == "16.0" ]; then
      echo
      #2020-03-05
      for com in 270110 270111 270112 270113 270114 270115 270116 270117 270118 270279 ; do
              repopick ${com} 2>&1
      done
      #2020-04-05
      for com in 272358 272359 272360 272361 272362 272363 272364 272560 ; do
              repopick ${com} 2>&1
      done
      echo
fi
if [ "${rev}" == "17.1" ]; then
      echo
      #soong: java: Specify larger heap size for metalava
      repopick -f 266411 2>&1
      echo
fi
echo
echo "The current security patch level for laos ${rev} is..."
grep "PLATFORM_SECURITY_PATCH := " build/core/version_defaults.mk
echo
while true; do
    read -p "Do you wish to build clean? Type Y/y or N/n or A/a to abort and hit return: " yna
    case $yna in
        [Yy]* ) echo; rm -rfv ./out; break;;
        [Nn]* ) break;;
        [Aa]* ) exit;;
    esac
done
echo
breakfast "${dev}"
croot
if [ "${thr}" == "" ]; then
	brunch "${dev}"
else
	breakfast "${dev}"
	make bacon -j "${thr}"
fi
cd "${OUT}" || exit
echo
echo "Press ENTER to continue..."
echo
read -s
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
        [Yy]* ) echo; rm -rfv "${HOME}/android/laos_${rev}/out"; break;;
        [Nn]* ) echo; break;;
    esac
done
