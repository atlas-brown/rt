#!/bin/bash
set -e

# H. Liu, April 27, 2020.
# Run downscaling regression year by year using GMET downscaling code.
# Reference: /home/hydrofcst/otl_support/forcings/GMET/run/run_ens_regr.csh

RootDir=/home/hongli/work/2020_04_21nldas_gmet

SourceDir=${RootDir}/scripts
GridInfo=${SourceDir}/conus_ens_grid_eighth_deg_v1p1.nc
StnlistDir=${SourceDir}/step4_sample_stnlist
StndataDir=${SourceDir}/step5_prepare_stndata

Program=${RootDir}/GMET_tpl/run/downscale.exe
Template=${SourceDir}/config/config.ens_regr.TEMPLATE.txt 

StartDateStn=20150101
EndDateStn=20161231

StartDateOut=20150101
EndDateOut=20150331

WorkDirBase=${RootDir}/test_uniform
if [ ! -d ${WorkDirBase} ]; then mkdir -p ${WorkDirBase}; fi

# loop all stnlist files
FILES=( $(ls ${StnlistDir}) )
FILE_NUM=${#FILES[@]}
for i in $(seq 0 $(($FILE_NUM -1))); do
    
    FileName=${FILES[${i}]}
    FileNameShort="${FileName/.txt/}" # remove suffix ".txt"
    GridNum=$(echo $FileNameShort| cut -d'_' -f 2) # extract substring "012grids"    
    CaseID=${GridNum}
    echo ${CaseID}

    # create work folders
    WorkDir=${WorkDirBase}/${CaseID}
    if [ ! -d ${WorkDir} ]; then mkdir ${WorkDir}; fi
    if [ ! -d ${WorkDir}/tmp ]; then mkdir ${WorkDir}/tmp; fi
    if [ ! -d ${WorkDir}/gmet_regr ]; then mkdir ${WorkDir}/gmet_regr; fi
    
    # configure stnlist and stndata
    StnList=$StnlistDir/$FileName
    StnDataDir=$StndataDir/stndata_${CaseID}
    WeightFile=${WorkDir}/gmet_regr/${CaseID}.bin
    
    # identify start and end time
    StartYr=$(echo $StartDateOut| cut -c1-4)
    EndYr=$(echo $EndDateOut| cut -c1-4)
    StMoDy=$(echo $StartDateOut| cut -c5-8)
    EndMoDy='1231'
    
    # loop through years
    for Y in $(seq ${StartYr} ${StartYr}); do
        echo $Y
        if [ $Y -gt ${StartYr} ]; then 
            StMoDy='0101'
        fi
        if [ $Y -eq ${EndYr} ]; then 
            EndMoDy=$(echo $EndDateOut| cut -c5-8)
        fi
        
        # configure config, output and log files
        ConfigFile=${WorkDir}/tmp/config.ens_regr.weight
        OutputFile=${WorkDir}/gmet_regr/regress_ts.weight.nc
        if [ -e ${OutputFile} ]; then rm -rf ${OutputFile}; fi
        
        sed "s,RunYr,$Y,g" $Template |\
        sed "s,StMoDy,$StMoDy,g" |\
        sed "s,EndMoDy,$EndMoDy,g" |\
        sed "s,StnList,$StnList,g" |\
        sed "s,GridInfo,$GridInfo,g" |\
        sed "s,OutputFile,$OutputFile,g" |\
        sed "s,StnDataDir,$StnDataDir,g" |\
        sed "s,StartDateStn,$StartDateStn,g" |\
        sed "s,EndDateStn,$EndDateStn,g" |\
        sed "s,FALSE,TRUE,g" |\
        sed "s,WeightFile,$WeightFile,g" > $ConfigFile

        # create job submission file
        CommandFile=${WorkDir}/tmp/sbatch.ens_regr.weight
        if [ -e ${command_file} ]; then rm -rf ${command_file}; fi
        
        LogFile=${WorkDir}/tmp/log.ens_regr.weight
        rm -f $LogFile.*

        echo '#!/bin/bash' > ${CommandFile}
        echo "#SBATCH --job-name=weight.${CaseID}" >> ${CommandFile}
        echo '#SBATCH --partition=main' >> ${CommandFile}
        echo '#SBATCH --ntasks=1' >> ${CommandFile}
        echo '#SBATCH --time=01:00:00' >> ${CommandFile}
        echo "#SBATCH --output=${LogFile}.%j" >> ${CommandFile}

        echo "${Program} ${ConfigFile}" >> ${CommandFile}
        chmod 740 ${CommandFile}
        
        sbatch ${CommandFile}
        
     done
done
