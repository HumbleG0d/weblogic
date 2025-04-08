#!/bin/bash

DOMAIN_NAME=OSB_Domain
JAR_FILE_NAME=OSB_Domain.jar
LOG_NAME=OSB_Domain.log
COMMON_DIR="/u01/oracle/product/osb1214/oracle_common/common/bin"
JAVA_HOME="/u01/oracle/product/jdk1.8.0_321/"
DOMAIN_BASE="/filestore"

error_handler(){
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a $LOG_FILE
    exit 1
}

[ -f "/home/weblogic/$JAR_FILE_NAME" ] || error_handler " El archivo jar no se encuentra"

echo " ====== Iniciando unpack ..... ====== "

cd "$COMMON_DIR" || error_handler "No se pudo acceder  a $COMMON_DIR "

./unpack.sh -domain="$DOMAIN_BASE/$DOMAIN_NAME" -template="/home/weblogic/$JAR_FILE_NAME" -java_home="$JAVA_HOME" -server_start_mode=prod -overwrite_domain=true -log="$LOG_NAME" -log_priority=info 

echo ' ========= unpack finalizado! ========= '

echo ' ========= Errollando nodos ========= '

##  POR AHORA ESYTO SERIA MANUAL 

"$COMMON_DIR/wslt.sh"

# connect('weblogic','weblogic1','t3://172.20.212.159:11000')

# nmEnroll()
# disconnect()
# exit()

echo ' ========= Configurando NodeManager ========= ' | tee -a $LOG_FILE

NM_DIR = "$DOMAIN_BASE/$DOMAIN_NAME/nodemanager"

[ -f "$NM_DIR/nodemanager.properties" ] || error_handler "Archivo de propiedades no encontrado"

sed -i \
    -e 's/SecureListener=true/SecureListener=false/' \
    "$NM_DIR/nodemanager.properties" || error_handler "Error modificando propiedades"

echo "==== Iniciando NodeManager ====" | tee -a $LOG_FILE
cd "$DOMAIN_BASE/$DOMAIN_NAME/bin" || error_handler "No se pudo acceder a bin/"

#nohup ./startNodeManager.sh > node_manager.log 2>&1 &
./startNodeManager.sh & tail -f nohup.out



