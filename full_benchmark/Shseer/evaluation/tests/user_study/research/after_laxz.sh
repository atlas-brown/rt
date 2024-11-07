#!/bin/bash
#last_used 1588951891 > 1588951891
#sed -i '3s|last_used|abcdef|1' laxz.config
#awk -F" " '{ print $2}' laxz.config
#echo "last used " `awk 'NR==3' laxz.config | cut -f 2 -d ' '`
user_files=/home/$USER/git-in-sync/workspace-bash/daily-bash
config_file=$user_files/laxz_config
source $config_file

now=`date "+%Y-%m-%d-%T"`
echo "last used $last_used"
sed -i "s/last_used=[^ ]*/last_used=$now/" $config_file

version='1.0.0' ;
developer='minlaxz :>' ;
AESKEY=$user_files/symme.key

usage(){
    echo "      --help      print laxz help message and exit." ;
    echo "      --version   print laxz version."
    echo "      --reset     no laxz hagas esto."

    echo "-h    --hardware  handle the hardware parts";
    echo "-n    --network   handle the networks." ;
    echo "-v    --virtual   virtual machine options.";
    echo "-z    --zip       zip any given file(s) or folder(s)." ;
    echo "-e    --encrypt   encrypt given {file} with aes256." ;
    echo "-d    --decrypt   decrypt laxz encrpyted {enc_file} aes256." ;
    echo "-r    --remove    safe remove to .trash unlike built-in 'rm'." ;
    echo "-p    --pkg       package update and upgrade." ;
    echo "-m    --mount     mount a network's samba drive.";
}
integrity(){
    echo "Original : $2 , CHECKSUM : $1 "
    echo "Modified : $4 , CHECKSUM : $3 "
}
encryptor(){
    echo "---enCRYption---" ;
    if [ $# -eq 0 ]; then
        echo "laxz -e {file} or {file_path}"
    else
        org_file=$1
        if [ ! -f $org_file ]; then
        echo "404."
        exit
        fi
        echo "encrypting file : '$org_file' with aes-256." ;
        read -p "encrypt with (p)assword or (k)eyfile ? : " uservar;
        case $uservar in
            [Pp]*) 
            #Password
            openssl aes-256-cbc -salt -pbkdf2 -in $org_file -out $org_file.loc;
            integrity `sha256sum $org_file` $(sha256sum $org_file.loc);
            echo "enCRYption Done." ;;
            
            [Kk]*)
            #keyfile
            if [ ! -f  $AESKEY ] ; then
            echo "AESKey not found!\nGenerating new one.\n";
            openssl rand 256 > symme.key ;
            openssl enc -aes-256-cbc -salt -pbkdf2 -in $org_file -out $org_file.locs -k $AESKEY ;
            else openssl enc -aes-256-cbc -salt -pbkdf2 -in $org_file -out $org_file.locs -k $AESKEY ; 
            fi
            integrity `sha256sum $org_file` $(sha256sum $org_file.locs);
            echo "enCRYption Done.";;
            
            *) echo "Aborded." ;;
        esac
    fi
}

decryptor(){
    echo "---deCRYption---" ;
    if [ $# -eq 0 ]; then
        echo "laxz -d {file} or {file_path}"
    else
        locked_file=$1
        if [ ! -f $locked_file ]; then
        echo "404. file input error"
        exit
        elif [[ $locked_file == *.loc ]]; then
            echo "encrypted with PASSWORD"
            openssl aes-256-cbc -d -salt -pbkdf2 -in $locked_file -out ${locked_file/.loc}
            integrity `sha256sum $locked_file` `sha256sum ${locked_file/.loc}`
        elif [[ $locked_file==*.locs ]] ; then
            echo "encrypted with KEY_FILE"
            if [ ! -f $AESKEY ] ; then
            echo "THIS IS FETAL, NO AES_KEY FOUND TO UNLOCK!"
            echo "make sure 'symme.key' file is accessible."
            else
            openssl enc -aes-256-cbc -d -salt -pbkdf2 -in $locked_file -out ${locked_file/.locs} -k $AESKEY
            integrity `sha256sum $locked_file` `sha256sum ${locked_file/.locs}`
            fi
        else
            echo "not a locked file."
            exit
        fi
    fi
}

zipper(){
    timenow=$(date +"%Y-%m-%d-%T") ;
    echo "---zip---" ;
    zip -r /home/$USER/laxz-$timenow.zip "$@" ;
    read -p "do you want to encrypt: y/n " uservar ;
    if [ $uservar == 'y' ];
    then encryptor /home/$USER/laxz-$timenow.zip ; 
    else printf "Cancel.";
    fi
}

mounter(){
    if [ $(id -u) != "0" ] ;
    then echo "Please run 'update option' as root" ;
    else
        if [ $1 != "" ] ; then
            mountpoint=$1
            sudo mount.cifs //192.168.0.10/samba_share $mountpoint -o user=laxzs,rw,pass=laxzsmb
        else
            echo "Specify the mount point."
        fi;
    fi;
}

iFunc(){
flag=$1
value=$2
    case "$flag" in
    "--monitor" | "-m" )
    #error -1, >= 10
        if [[ $value == "" || $value < 0.5 || $value > 1.3 ]] ; then #|| $value =~ ^[-+]?[0-9]+$
        echo "brightness $value {value error}."
        else
        echo "previous brightness : $brightness"
        echo "current brightess : $value"
        port=$(xrandr -q | grep ' connected' | head -n 1 | cut -d ' ' -f1);
        echo "port detected : $port";
        xrandr --output $port --brightness $value;
        sed -i "s/brightness=[^ ]*/brightness=$value/" $config_file
        echo "all set."
        fi
        ;;
    *)
        echo "error"
        ;;
    esac
}
version(){
    echo "Version : $version" ;
}

developer(){
    notify-send 'Developed by' 'minlaxz'
    echo -e "\a"
    echo "Developed by : $developer" ;
}

if [ $# -eq 0 ]; then
    echo "[--help] for usage." ;
    echo "[--version] check version." ;
else
    case "$1" in
        
        --help) usage ;;
        --version) version ;;
        --developer) developer ;;
        --reset) reset ;;

        -e | --encrypt) encryptor $2 ;;
        -d | --decrypt) decryptor $2 ;;
        -z | --zip) zipper $* ;;

        -h | --hardware)
        if [[ $2 == "-m" || $2 == "--monitor" ]] ; then
            if [[ $3 == "" ]] ; then
            read -p 'set brightness 0.5 ~ 1.3 : ' br ;
            iFunc $2 $br
            else
            iFunc $2 $3
            fi
        else
        echo "iFunc bypassed."
        bash $user_files/hardware-handling.sh
        fi 
        ;;
        -n | --network) bash $user_files/network-handling.sh ;;
        -p | --pkg) bash $user_files/package-handling.sh ;;
        -v | --virtual) bash $user_files/vm-handling.sh ;;

        
        -m | --mount) mounter $2 ;;
        -r | --remove) 
        if [[ `apt list --installed trash-cli 2>/dev/null | wc -l` == 1 ]] ; then
        sudo apt install trash-cli #Thanks https://github.com/andreafrancia/trash-cli
        else
        trash-put "$@"
        fi
        echo "removed to Trash."
        ;;
        *) echo "Option $1 not recognized" ;;
        
    esac
fi