#!/bin/bash
BROWN='\033[0;33m'
NC='\033[0m'
GREEN='\033[0;32m'
org_pth=""
EXT_NW=""
D_STK=""
PEER_CONN_PARMS=""
#declare -A orgs
function sendTokenToOrgs() {
    ./dockerSetup.sh "sendJoinToken" ${orgs[@]}
}
function startSwarmNetwork() {
    Cr_D=$PWD
    cd $1
    EXT_NW=$2
    orgs=("${@:3}")
    chmod +x ./dockerSetup.sh 
    chmod +x ./buildingNetwork.sh
    ./dockerSetup.sh "swarmCreate" ${EXT_NW}
    #sendTokenToOrgs
  cd $Cr_D
}

function startComposeNetwork () {
    Cr_D=$PWD
    EXT_NW=$2
    cd $1
    chmod +x ./dockerSetup.sh 
    chmod +x ./buildingNetwork.sh
    ./dockerSetup.sh "deployCompose" ${EXT_NW}
    #sendTokenToOrgs
    cd $Cr_D
}
function startService() {
    Cr_D=$PWD
    cd $org_pth
    chmod +x ./dockerSetup.sh 
    ./dockerSetup.sh "deployServices" ${D_STK}
    cd $Cr_D
}
function startCompose() {
    Cr_D=$PWD
    cd $org_pth
    chmod +x ./dockerSetup.sh 
    export COMPOSE_PROJECT_NAME=clif
    ./dockerSetup.sh "deployCompose" $EXT_NW
    cd $Cr_D
}
function deployNetwork() {
    CLI_CONTAINER=$(docker ps |grep ${D_NME}_cli|awk '{print $1}')
    if [ "${CLI_CONTAINER}" == "" ]; then
    echo -e "${RED}CONTAINER NOT found !!! ${NC}"
    exit 1
    fi
    docker exec ${CLI_CONTAINER} ./buildingNetwork.sh $CH_NME $D_NME $P_CT "false"
    if [ $? -ne 0 ]; then
        echo "ERROR !!!! failed"
        exit 1
    fi
}
function installCCinChannel() {
    echo $@
    CH_NME=$1
    D_NME=$2
    P_CT=$3
    DD_type=$4
    CC_NAME=$5
    CC_VER=$6
    CC_S_P=$7
    C_LANG=$8
    isMain=$9
    if [ ${isMain} == true ];then
        CLI_CC=$(docker ps |grep ${D_NME}_cli|awk '{print $1}')
        docker exec $CLI_CC ./buildingNetwork.sh $CH_NME $D_NME $P_CT "false" "no policy" $CC_NAME $CC_VER $CC_S_P $C_LANG "true"
    else
        if [ "$DD_type" == "Docker-swarm-m" ]; then
            SSH_dORG=${10}
            INS_CNTR_ID=$(ssh $SSH_dORG docker ps|grep ${D_NME}_cli|awk '{print $1}')
        echo $INS_CNTR_ID
        ssh $SSH_dORG /bin/bash << EOF
cd ./CLIF/${D_NME}/;
./dockerSetup.sh "installCC" $D_NME $CH_NME $P_CT $CC_NAME $CC_VER $CC_S_P $C_LANG
EOF
        else
            cr=$PWD
            cd ~/CLIF/${D_NME}/;
            ./dockerSetup.sh "installCC" $D_NME $CH_NME $P_CT $CC_NAME $CC_VER $CC_S_P $C_LANG
            cd $cr
        fi
    fi
}
function packageCC() {
    echo $@
    CH_NME=$1
    D_NME=$2
    CC_NAME=$3
    CC_VER=$4
    CC_S_P=$5
    C_LANG=$6
    CLI_CC=$(docker ps |grep ${D_NME}_cli|awk '{print $1}')
    echo '##########################################'
    echo '# Installing Build Tools'
    echo '##########################################'   
    #docker exec $CLI_CC go get github.com/hyperledger/fabric-chaincode-go/shim
    if [ $? -ne 0 ]; then
        echo "ERROR !!!! failed to get build toools"
        exit 1
    fi
    echo '##########################################'
    echo '# Packaging Chaincode'
    echo '##########################################' 
    echo "${NC}+ peer lifecycle chaincode package ${CC_NAME}.tar.gz -p /opt/gopath/src/${CC_S_P} -l ${C_LANG} --label ${CC_NAME}_${CC_VER}"
    docker exec -ti $CLI_CC peer lifecycle chaincode package ${CC_NAME}.tar.gz -p /opt/gopath/src/${CC_S_P} -l ${C_LANG} --label ${CC_NAME}_${CC_VER}
    if [ $? -ne 0 ]; then
        echo "ERROR !!!! failed To generate Chaincode Package"
        exit 1
    fi
}
function installPackage() {
    echo $@
    CH_NME=$1
    D_NME=$2
    P_CT=$3
    DD_type=$4
    CC_NAME=$5
    CC_VER=$6
    CC_S_P=$7
    C_LANG=$8
    isMain=$9
    M_ORG=${10}
    if [ ${isMain} == true ];then
        CLI_CC=$(docker ps |grep ${D_NME}_cli|awk '{print $1}')
        docker exec $CLI_CC ./buildingNetwork.sh $CH_NME $D_NME $P_CT "false" "no policy" $CC_NAME $CC_VER $CC_S_P $C_LANG "true"
        # docker exec $CLI_CC peer lifecycle chaincode install ${CC_NAME}.tar.gz
        docker cp ${CLI_CC}:/opt/gopath/src/github.com/hyperledger/fabric/peer/${CC_NAME}.tar.gz ~/CLIF/${D_NME}/${CC_NAME}.tar.gz
    else
        if [ "$DD_type" == "Docker-swarm-m" ]; then
            SSH_dORG=${11}
            INS_CNTR_ID=$(ssh $SSH_dORG docker ps|grep ${D_NME}_cli|awk '{print $1}')
            echo $INS_CNTR_ID
            scp -r ~/CLIF/${M_ORG}/${CC_NAME}.tar.gz ${INS_CNTR_ID}:./CLIF/${D_NME}/${CC_NAME}.tar.gz
            ssh $SSH_dORG /bin/bash << EOF
cd ./CLIF/${D_NME}/;
./dockerSetup.sh "installCC" $D_NME $CH_NME $P_CT $CC_NAME $CC_VER $CC_S_P $C_LANG
EOF
        else
            cr=$PWD
            cp -r ~/CLIF/${M_ORG}/${CC_NAME}.tar.gz ~/CLIF/${D_NME}/${CC_NAME}.tar.gz
            cd ~/CLIF/${D_NME}/;
            ./dockerSetup.sh "installCC" $D_NME $CH_NME $P_CT $CC_NAME $CC_VER $CC_S_P $C_LANG
            cd $cr
        fi
    fi
}

function approvePackage() {
    echo $@
    CH_NME=$1
    D_NME=$2
    P_CT=$3
    DD_type=$4
    CC_NAME=$5
    CC_VER=$6
    CC_S_P=$7
    C_LANG=$8
    isMain=$9
    if [ ${isMain} == true ];then
        CLI_CC=$(docker ps |grep ${D_NME}_cli|awk '{print $1}')
        docker exec $CLI_CC ./buildingNetwork.sh $CH_NME $D_NME $P_CT "false" "no policy" $CC_NAME $CC_VER $CC_S_P $C_LANG "approve"
        # docker exec $CLI_CC peer lifecycle chaincode install ${CC_NAME}.tar.gz
        docker cp ${CLI_CC}:/opt/gopath/src/github.com/hyperledger/fabric/peer/${CC_NAME}.tar.gz ~/CLIF/${D_NME}/${CC_NAME}.tar.gz
    else
        if [ "$DD_type" == "Docker-swarm-m" ]; then
            SSH_dORG=${10}
            INS_CNTR_ID=$(ssh $SSH_dORG docker ps|grep ${D_NME}_cli|awk '{print $1}')
            echo $INS_CNTR_ID
            #scp -r ~/CLIF/${M_ORG}/${CC_NAME}.tar.gz ${SSH_dORG}:./CLIF/${D_NME}/${CC_NAME}.tar.gz
            # ssh $SSH_dORG docker exec ${INS_CNTR_ID} peer lifecycle chaincode install ${CC_NAME}.tar.gz
             ssh $SSH_dORG /bin/bash << EOF
cd ./CLIF/${D_NME}/;
./dockerSetup.sh "approveCC" $D_NME $CH_NME $P_CT $CC_NAME $CC_VER $CC_S_P $C_LANG
EOF
        else
            cr=$PWD
            cd ~/CLIF/${D_NME}/;
            ./dockerSetup.sh "approveCC" $D_NME $CH_NME $P_CT $CC_NAME $CC_VER $CC_S_P $C_LANG
            cd $cr
        fi
    fi
    
}
parsePeerConnectionParameters() {
    echo $@
    D_NME=$1
    DD_type=$2
    isMain=$3
    M_ORG=$4 
    if [ ${isMain} == true ];then
        PEER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/peerOrganizations/${D_NME}.example.com/peers/peer0.${D_NME}.example.com/tls/ca.crt
        PEER_CONN_PARMS="$PEER_CONN_PARMS --peerAddresses peer0.${D_NME}.example.com:7051"
        ## Set path to TLS certificate
        TLSINFO=$(eval echo "--tlsRootCertFiles \$PEER_CA")
        PEER_CONN_PARMS="$PEER_CONN_PARMS $TLSINFO"
    else
        if [ "$DD_type" == "Docker-swarm-m" ]; then
            SSH_dORG=${5}
            INS_CNTR_ID=$(ssh $SSH_dORG docker ps|grep ${D_NME}_cli|awk '{print $1}')
            echo $INS_CNTR_ID
            scp -r ${SSH_dORG}:./CLIF/${D_NME}/crypto-config/peerOrganizations/${D_NME}.example.com ~/CLIF/${M_ORG}/crypto-config/peerOrganizations/${D_NME}.example.com
            PEER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/peerOrganizations/${D_NME}.example.com/peers/peer0.${D_NME}.example.com/tls/ca.crt
            PEER_CONN_PARMS="$PEER_CONN_PARMS --peerAddresses peer0.${D_NME}.example.com:7051"
            ## Set path to TLS certificate
            TLSINFO=$(eval echo "--tlsRootCertFiles \$PEER_CA")
            PEER_CONN_PARMS="$PEER_CONN_PARMS $TLSINFO"
        else
            cp -rf ~/CLIF/${D_NME}/crypto-config/peerOrganizations/${D_NME}.example.com ~/CLIF/${M_ORG}/crypto-config/peerOrganizations/${D_NME}.example.com
            PEER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/peerOrganizations/${D_NME}.example.com/peers/peer0.${D_NME}.example.com/tls/ca.crt
            PEER_CONN_PARMS="$PEER_CONN_PARMS --peerAddresses peer0.${D_NME}.example.com:7051"
            ## Set path to TLS certificate
            TLSINFO=$(eval echo "--tlsRootCertFiles \$PEER_CA")
            PEER_CONN_PARMS="$PEER_CONN_PARMS $TLSINFO"
        fi
    fi  
}
commitChaincode() {
     echo $@
    CH_NME=$1
    D_NME=$2
    P_CT=$3
    CC_NAME=$4
    CC_VER=$5
    CC_S_P=$6
    C_LANG=$7
    CLI_CC=$(docker ps |grep ${D_NME}_cli|awk '{print $1}')
    docker exec $CLI_CC ./buildingNetwork.sh $CH_NME $D_NME $P_CT "true" "nopolicy" $CC_NAME $CC_VER $CC_S_P $C_LANG "false" $PEER_CONN_PARMS
    # docker exec $CLI_CC peer lifecycle chaincode install ${CC_NAME}.tar.gz
}
function instantiateChainIntoChannel() {
    echo $@
    CH_NME=$1
    D_NME=$2
    P_CT=$3
    POLICY=$4
    CC_NAME=$5
    CC_VER=$6
    CC_S_P=$7
    CC_LANG=$8
    # -P "OR ('Org1MSP.peer','Org2MSP.peer')"
    CLI_CONTAINER=$(docker ps |grep ${D_NME}_cli|awk '{print $1}')
    if [ "${CLI_CONTAINER}" == "" ]; then
    echo -e "${RED}CONTAINER NOT found !!! ${NC}"
    exit 1
    fi
    docker exec ${CLI_CONTAINER} ./buildingNetwork.sh $CH_NME $D_NME $P_CT true "$POLICY" $CC_NAME $CC_VER $CC_S_P $CC_LANG  
    if [ $? -ne 0 ]; then
        echo "ERROR !!!! failed"
        exit 1
    fi
}

function runMainNetwork() {
    echo $@
    org_pth=$1
    EXT_NW=$2
    D_STK=$8
    CH_NME=$3
    D_NME=$4
    # CC_S_P=github.com/chaincode/chaincode_example02/go/
    # CC_VER=$5
    ORD_adr=$5
    P_CT=$6
    n_tpe=$7
    #startSwarmNetwork
    echo ${n_tpe}
    if [ "${n_tpe}" == "Docker-compose" ]; then
        echo "Starting Compose Network "
    else
        startService
    fi
    deployNetwork
}
function sendOrderer() {
    if [ "$3" == "Docker-swarm-m" ]; then
        scp -r ~/CLIF/$1/crypto-config/ordererOrganizations $4:./CLIF/$2/crypto-config/
    else
        cp -rf ~/CLIF/$1/crypto-config/ordererOrganizations ~/CLIF/$2/crypto-config/
    fi
}
function addNewOrg() {
    M_ORG=$1
    ad_Org=$2
    CH_NME=$3
    O_TPE=$4
    AP_cnt=$5
    DEP_TYPE=$6
    OG_SSH_ADD=$7
    if [ ! -f "${ad_Org}.json" ]; then
        if [ "$DEP_TYPE" == "Docker-swarm-m" ]; then
            scp $OG_SSH_ADD:./CLIF/$ad_Org/${ad_Org}.json ~/CLIF/${M_ORG}/
            sendOrderer $M_ORG $ad_Org $DEP_TYPE $OG_SSH_ADD
        else
            cp ~/CLIF/${ad_Org}/${ad_Org}.json ~/CLIF/${M_ORG}/
            sendOrderer $M_ORG $ad_Org
        fi
    fi
    CLI_CONTAINER=$(docker ps |grep ${M_ORG}_cli|awk '{print $1}')
    if [ "${CLI_CONTAINER}" == "" ]; then
    echo -e "${RED}CONTAINER NOT found !!! ${NC}"
    exit 1
    fi
    docker exec ${CLI_CONTAINER} ./addNewOrg.sh $ad_Org $CH_NME $O_TPE $AP_cnt $M_ORG
    if [ $? -ne 0 ]; then
        echo "ERROR !!!! failed"
        exit 1
    fi
}

function AddOrgToNetwork() {
    echo $@
    ad_Org=$1
    CH_NME=$2
    O_TPE=$3
    N_TYPE=$4
    EXT_NW=$5
    DS_NAME=$7
    if [ "${O_TPE}" == "KAFKA" ]; then
        OR_AD="orderer0"
    else
        OR_AD="orderer0"
    fi
    AP_CN=$6
    OG_SSH_ADD=$8
    M_OG=$9
    if [ "$N_TYPE" == "Docker-swarm-m" ]; then
        #echo ""buildNetwork" ${DS_NAME} ${ad_Org} ${CH_NME} ${CC_NAME} ${CC_VER} ${OR_AD} "github.com/chaincode/chaincode_example02/go/" $AP_CN $N_TYPE $EXT_NW"
        scp ~/CLIF/$M_OG/tokenToJoinNetwork.sh $OG_SSH_ADD:./CLIF/$ad_Org/
        ssh $OG_SSH_ADD /bin/bash << EOF
cd ./CLIF/$ad_Org/;
chmod +x tokenToJoinNetwork.sh;
./tokenToJoinNetwork.sh;
./dockerSetup.sh "buildNetwork" $EXT_NW ${ad_Org} ${CH_NME} ${OR_AD} $AP_CN $N_TYPE ${DS_NAME}
EOF
    else
        c_path=$PWD
        cd ~/CLIF/${ad_Org}/
        #echo ""buildNetwork" ${DS_NAME} ${ad_Org} ${CH_NME} ${CC_NAME} ${CC_VER} ${OR_AD} "github.com/chaincode/chaincode_example02/go/" $AP_CN $N_TYPE $EXT_NW"
        export COMPOSE_PROJECT_NAME=clif
        ./dockerSetup.sh "buildNetwork" $EXT_NW ${ad_Org} ${CH_NME} ${OR_AD} $AP_CN $N_TYPE ${DS_NAME}
        cd $c_path
    fi
}
function updateChannelConfig() {
    m_org=$1
    ad_org=$2
    CH_NME=$3
    DN_TYPE=$4
    DN_ORG_SSH=$5
    tr="$"
    cat << EOF > ./updateChannelConfig.sh
#!/bin/bash
CHANNEL_NAME=${tr}2
DOMAIN=${tr}1
ORDERER_URL=orderer0.example.com
ORDERER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer0.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
peer channel update -f ${tr}{DOMAIN}_update_in_envelope.pb -c ${tr}CHANNEL_NAME -o ${tr}ORDERER_URL:7050 --tls --cafile ${tr}ORDERER_CA 2>&1
if [ ${tr}? -ne 0 ];then
  echo "******************** FAILED TO ADD ${tr}DOMAIN INTO THE NETWORK *********************"
  exit 1
else
  echo "******************** ${tr}{DOMAIN} ORGANISATION ADDED TO NETWORK **********************"
fi
exit 0
EOF
echo "DN_ORG_SSH=${DN_ORG_SSH}"
chmod +x ./updateChannelConfig.sh
    if [ "${DN_ORG_SSH}" != "" ]; then
        scp ./updateChannelConfig.sh $DN_ORG_SSH:./CLIF/$m_org/
        rm ./updateChannelConfig.sh
        scp ./updateChannelConfig.sh $DN_ORG_SSH:./CLIF/$m_org/
        M_C_ID=$(ssh $DN_ORG_SSH docker ps|grep ${m_org}_cli|awk '{print $1}')
        echo $M_C_ID
        ssh $DN_ORG_SSH /bin/bash << EOF
docker exec $M_C_ID ./updateChannelConfig.sh $ad_Org $CH_NME;
EOF
   else
        cp ./updateChannelConfig.sh ~/CLIF/${m_org}/
        rm ./updateChannelConfig.sh
        CLI_CONTAINER=$(docker ps |grep ${m_org}_cli|awk '{print $1}')
        if [ "${CLI_CONTAINER}" == "" ]; then
            echo -e "${RED}CONTAINER NOT found !!! ${NC}"
            exit 1
        fi
        docker exec ${CLI_CONTAINER} ./updateChannelConfig.sh $ad_Org $CH_NME
        if [ $? -ne 0 ]; then
            echo -e "${RED}ERROR !!!! failed to add organisation${NC}"
            exit 1
        fi
    fi
}

function signChannelConfig() {
    m_org=$1
    ad_org=$2
    CH_NME=$3
    sin_org=$4
    p_cnt=$5
    DN_TYPE=$6
    DN_ORG_SSH=$8
    ROOT_ORG=$7
    tr="$"
    cat << EOF > ./signChannelConfig.sh
#!/bin/bash
P_CN=${tr}1
M_DMIN=${tr}2
DOMAIN=${tr}3
peer=0
while [ "${tr}peer" != "${tr}P_CN" ]
do
    export CORE_PEER_ADDRESS=peer${tr}peer.${tr}{M_DMIN}.example.com:7051
    peer channel signconfigtx -f ${tr}{DOMAIN}_update_in_envelope.pb
    peer=${tr}(expr ${tr}peer + 1)
done
export CORE_PEER_ADDRESS=peer0.${tr}{M_DMIN}.example.com:7051
exit 0
EOF
chmod +x ./signChannelConfig.sh
d_pth=/opt/gopath/src/github.com/hyperledger/fabric/peer/
if [ "${DN_ORG_SSH}" != "" ]; then
   scp ./signChannelConfig.sh $DN_ORG_SSH:./CLIF/$ad_org/
    rm ./signChannelConfig.sh
    R_C_ID=$(docker ps |grep ${ROOT_ORG}_cli|awk '{print $1}')
    docker cp $R_C_ID:$d_pth/${sin_org}_update_in_envelope.pb ~/CLIF/${ROOT_ORG}/${sin_org}_update_in_envelope.pb
    scp ~/CLIF/${ROOT_ORG}/${sin_org}_update_in_envelope.pb $DN_ORG_SSH:./CLIF/${ad_org}/${sin_org}_update_in_envelope.pb
    M_C_ID=$(ssh $DN_ORG_SSH docker ps|grep ${ad_org}_cli|awk '{print $1}')
    echo $M_C_ID    
    ssh $DN_ORG_SSH /bin/bash << EOF
docker cp ~/CLIF/${ad_org}/${sin_org}_update_in_envelope.pb $M_C_ID:$d_pth/${sin_org}_update_in_envelope.pb
EOF
    ssh $DN_ORG_SSH /bin/bash << EOF
docker exec ${M_C_ID} ./signChannelConfig.sh $p_cnt $ad_org $sin_org;
docker cp $M_C_ID:$d_pth/${sin_org}_update_in_envelope.pb  ./CLIF/${ad_org}/${sin_org}_update_in_envelope.pb
EOF
    rm -f ~/CLIF/${ROOT_ORG}/${sin_org}_update_in_envelope.pb
    scp $DN_ORG_SSH:./CLIF/${ad_org}/${sin_org}_update_in_envelope.pb ~/CLIF/${ROOT_ORG}/${sin_org}_update_in_envelope.pb
else

cp ./signChannelConfig.sh ~/CLIF/$ad_org/
rm ./signChannelConfig.sh
M_C_ID=$(docker ps |grep ${m_org}_cli|awk '{print $1}')
 if [ "${M_C_ID}" == "" ]; then
    echo -e "${RED}CONTAINER NOT found !!! ${NC}"
    exit 1
fi
A_C_ID=$(docker ps |grep ${ad_org}_cli|awk '{print $1}')
 if [ "${A_C_ID}" == "" ]; then
    echo -e "${RED}CONTAINER NOT found !!! ${NC}"
    exit 1
fi
docker cp $M_C_ID:$d_pth/${sin_org}_update_in_envelope.pb ~/CLIF/${m_org}/${sin_org}_update_in_envelope.pb
docker cp ~/CLIF/${m_org}/${sin_org}_update_in_envelope.pb $A_C_ID:$d_pth 2>&1
    if [ $? -ne 0 ]; then
        echo "ERROR !!!! failed"
        exit 1
    fi
docker exec ${A_C_ID} ./signChannelConfig.sh $p_cnt $ad_org $sin_org
    if [ $? -ne 0 ]; then
        echo "ERROR !!!! failed"
        exit 1
    fi
fi
}
