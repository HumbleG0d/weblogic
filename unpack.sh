#!/bin/bash

#Variables
DOMAIN_NAME=PostventaEAI_001
JAR_FILE_NAME=PostventaEAI_001.jar
COMMON_DIR="/u01/oracle/product/wls12214/oracle_common/common/bin"
DOMAIN_DIR="/u01/oracle/domains"


error_acceso_directorio(){
    echo "Error: ($?) $1"
    exit 1
}


cd "$COMMON_DIR"
./unpack.sh -domain="/filestore/$DOMAIN_NAME" -template="/home/weblogic/$JAR_FILE_NAME"

echo '==== Modificando el nodemananger.properties'

cd "/filestore/$DOMAIN_NAME/nodemanager" || error_acceso_directorio

sed -i 's/SecureListener=true/SecureListener=false/' nodemananger.properties


echo '==== Levantando el nodo ===='

cd .. 
cd bin/
./startNodeManager.sh & tail -f nohup.out

#scp script_local.sh usuario@servidor:~/ && ssh usuario@servidor 'bash ~/script_local.sh'
