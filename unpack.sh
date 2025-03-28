#!/bin/bash

DOMAIN_NAME="PostventaEAI_001"
JAR_FILE_NAME="PostventaEAI_001.jar"
COMMON_DIR="/u01/oracle/product/wls12214/oracle_common/common/bin"
DOMAIN_BASE="/filestore"
LOG_FILE="/tmp/weblogic_unpack_$(date +%Y%m%d).log"

# Función de error mejorada
error_handler() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a $LOG_FILE
    exit 1
}

[ -f "/home/weblogic/$JAR_FILE_NAME" ] || error_handler "Archivo JAR no encontrado"
[ -d "$COMMON_DIR" ] || error_handler "Directorio de binarios no existe"

echo "==== Ejecutando unpack del dominio ====" | tee -a $LOG_FILE
cd "$COMMON_DIR" || error_handler "No se pudo acceder a $COMMON_DIR"

./unpack.sh \
    -domain="$DOMAIN_BASE/$DOMAIN_NAME" \
    -template="/home/weblogic/$JAR_FILE_NAME" \
    >> $LOG_FILE 2>&1 || error_handler "Falló el comando unpack"

echo "==== Configurando NodeManager ====" | tee -a $LOG_FILE
NM_DIR="$DOMAIN_BASE/$DOMAIN_NAME/nodemanager"

[ -f "$NM_DIR/nodemanager.properties" ] || error_handler "Archivo de propiedades no encontrado"

sed -i \
    -e 's/SecureListener=true/SecureListener=false/' \
    "$NM_DIR/nodemanager.properties" || error_handler "Error modificando propiedades"

echo "==== Iniciando NodeManager ====" | tee -a $LOG_FILE
cd "$DOMAIN_BASE/$DOMAIN_NAME/bin" || error_handler "No se pudo acceder a bin/"

nohup ./startNodeManager.sh > node_manager.log 2>&1 &

# Verificación de inicio
sleep 10 # Esperar para que inicie
if ! pgrep -f "weblogic.NodeManager" >/dev/null; then
    error_handler "NodeManager no se inició correctamente"
fi

echo "==== Proceso completado exitosamente ====" | tee -a $LOG_FILE