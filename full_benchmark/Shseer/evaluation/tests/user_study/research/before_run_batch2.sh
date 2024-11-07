#!/bin/bash
export PYTHONUNBUFFERED=true

#mva="wv_BDTG6"
#mva="wjj_BDTG6"
mva="None"

boson="Z"
#boson="W"

year="2016"
#year="2017"
#year="2018"

#region_list=("cr_wjets_wv_01" "cr_top_wv_01" "train_wv_01")
#region_list=("cr_wjets_wjj_01" "cr_top_wjj_01" "train_wjj_01")
#region_list=("cr_wjets_zv_01" "cr_top_zv_01" "train_zv_01")
region_list=("cr_wjets_zjj_01" "cr_top_zjj_01" "train_zjj_01")

applyL1Weight=false
do_train_systematics=false

#####################

if [[ $applyL1Weight == true ]]; then
    L1PF="--apply-L1PF"
else
    L1PF=""
fi
echo "selected L1PF: ${L1PF}"

for region in "${region_list[@]}"; do
    echo "for loop region: ${region}"
    systematics=("")

    if [[ "${region}" == "train"* ]] && [[ $do_train_systematics == true ]]; then
        systematics=("" "jesUp" "jesDown")
    fi
    echo "selected systematics: ${systematics}"

    for sys in "${systematics[@]}"; do
        echo "for loop systematics: ${sys}"

        if [[ "${sys}" == "" ]]; then
            fileTag=${mva}
        else
            fileTag=${sys}_${mva}
        fi
        echo "selected fileTag: ${fileTag}"

        if [[ ${fileTag} == "None" ]]; then
            dataset_awkd="df_dataset_${year}.awkd"
        else
            dataset_awkd="df_dataset_${year}_${fileTag}.awkd"
        fi
        echo "selected dataset_awkd: ${dataset_awkd}"

        for lep in "e" "m"; do
            echo "for loop lepton: ${lep}"
            echo "selected boson: ${boson}"
           ./make_hists.py --dframes $dataset_awkd \
           --lepton ${lep} --boson ${boson} --region ${region} --info_out ${fileTag} ${L1PF}
        done

        hadd -f ${region}_${fileTag}.root ${region}_${fileTag}_e.root ${region}_${fileTag}_m.root

        rootmkdir -p ${region}_${mva}_${year}.root:${sys}/_e/
        rootmkdir -p ${region}_${mva}_${year}.root:${sys}/_m/

        rootcp ${region}_${fileTag}.root:* ${region}_${mva}_${year}.root:${sys}/
        rootcp ${region}_${fileTag}_e.root:* ${region}_${mva}_${year}.root:${sys}/_e/
        rootcp ${region}_${fileTag}_m.root:* ${region}_${mva}_${year}.root:${sys}/_m/

        rm ${region}_${fileTag}.root
        rm ${region}_${fileTag}_e.root
        rm ${region}_${fileTag}_m.root
    done
done
