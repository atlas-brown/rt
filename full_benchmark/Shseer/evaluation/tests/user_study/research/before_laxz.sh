#!/bin/bash
version='1.0.0' ;
developer='minlaxz :>' ;
thispath=/home/$USER/git-in-sync/workspace-bash/daily-bash/
AESKEY=/home/$USER/symme.key
usage(){
    echo "-h, --help, print this help message and exit." ;
    echo "-v, --version, print version."

    echo "-k, --kit, handle the hardware parts";
    echo "-n, --network, handle the networks." ;
    echo "-v, --virtual, virtual machine options.";
    echo "-z, --zip, zip any given file(s) or folder(s)." ;
    echo "-e, --encrypt, encrypt given {file} with aes256." ;
    echo "-d, --decrypt, decrypt laxz encrpyted {enc_file} aes256." ;
    echo "-r, --remove, safe remove to .trash unlike built-in 'rm'." ;
    echo "-p, --pkg, pkg update and upgrade." ;
    echo "-m, --mount, mount a network's samba drive.";
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

remover(){
    mv "$@" /home/$USER/.trash ;
    echo "removed to Trash." ;
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

version(){
    echo "Version : $version" ;
}

developer(){
    notify-send 'Developed by' 'minlaxz'
    echo -e "\a"
    echo "Developed by : $developer" ;
}

if [ $# -eq 0 ]; then
    echo "[-h, --help] for usage." ;
    echo "[-v, --version] check version." ;
else
    case "$1" in
        
        -h | --help) usage ;;
        -V | --version) version ;;
        --developer) developer ;;

        -e | --encrypt) encryptor $2 ;;
        -d | --decrypt) decryptor $2 ;;
        -z | --zip) zipper $* ;;

        -k | --kit) bash $thispath/sys-dev.sh $2 ;;
        -n | --network) bash $thispath/network-handling.sh ;;
        -p | --pkg) bash $thispath/package-handling.sh ;;
        -v | --virtual) bash $thispath/vm-handling.sh ;;

        
        -m | --mount) mounter $2 ;;
        -r | --remove) remover $* ;;
        *) echo "Option $1 not recognized" ;;
        
    esac
fi