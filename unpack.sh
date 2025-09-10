#!/bin/bash

# Configuración
DOMAIN_NAME="OSB_Domain"
JAR_FILE_NAME="OSB_Domain.jar"
LOG_FILE="OSB_Domain.log"
COMMON_DIR="/u01/oracle/product/osb1214/oracle_common/common/bin"
JAVA_HOME="/u01/oracle/product/jdk1.8.0_321/"
DOMAIN_BASE="/filestore"
ADMIN_URL=""
ADMIN_USER="weblogic"
ADMIN_PASS="weblogic1"

error_handler() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a $LOG_FILE
    exit 1
}

CURRENT_NODE_IP=$(hostname -I | awk '{print $1}')
[ -z "$CURRENT_NODE_IP" ] && error_handler "No se pudo determinar la IP del nodo actual"

echo "====== Configurando nodo $CURRENT_NODE_IP ======" | tee -a $LOG_FILE

[ -f "/home/weblogic/$JAR_FILE_NAME" ] || error_handler "El archivo jar no se encuentra"

echo "====== Iniciando unpack... ======" | tee -a $LOG_FILE

cd "$COMMON_DIR" || error_handler "No se pudo acceder a $COMMON_DIR"

./unpack.sh -domain="$DOMAIN_BASE/$DOMAIN_NAME" \
            -template="/home/weblogic/$JAR_FILE_NAME" \
            -java_home="$JAVA_HOME" \
            -server_start_mode=prod \
            -overwrite_domain=true \
            -log="$LOG_FILE" \
            -log_priority=info || error_handler "Error al ejecutar unpack"

echo "========= Unpack finalizado! =========" | tee -a $LOG_FILE

# Función para enrollar el nodo actual
enroll_current_node() {
    echo "Enrollando nodo actual ($CURRENT_NODE_IP)..." | tee -a $LOG_FILE
    
    # Crear script WLST temporal
    TMP_SCRIPT=$(mktemp)
    cat <<EOF > "$TMP_SCRIPT"
connect('$ADMIN_USER', '$ADMIN_PASS', '$ADMIN_URL')
nmEnroll('$DOMAIN_BASE/$DOMAIN_NAME', '$DOMAIN_BASE/$DOMAIN_NAME/nodemanager')
disconnect()
exit()
EOF

    # Ejecutar WLST con el script temporal
    "$COMMON_DIR/wlst.sh" "$TMP_SCRIPT" | tee -a $LOG_FILE
    
    # Limpiar script temporal
    rm -f "$TMP_SCRIPT"
    
    # Verificar si el enroll fue exitoso
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        error_handler "Error al enrollar nodo $CURRENT_NODE_IP"
    fi
    
    echo "Nodo $CURRENT_NODE_IP enrollado exitosamente" | tee -a $LOG_FILE
}

enroll_current_node

echo "========= Configurando NodeManager =========" | tee -a $LOG_FILE

NM_DIR="$DOMAIN_BASE/$DOMAIN_NAME/nodemanager"

[ -f "$NM_DIR/nodemanager.properties" ] || error_handler "Archivo de propiedades no encontrado"

# Modificar propiedades de NodeManager
sed -i \
    -e 's/SecureListener=true/SecureListener=false/' \
    -e "s/ListenAddress=.*/ListenAddress=$CURRENT_NODE_IP/" \
    "$NM_DIR/nodemanager.properties" || error_handler "Error modificando propiedades"

echo "==== Iniciando NodeManager ====" | tee -a $LOG_FILE
cd "$DOMAIN_BASE/$DOMAIN_NAME/bin" || error_handler "No se pudo acceder a bin/"

nohup ./startNodeManager.sh > "$DOMAIN_BASE/$DOMAIN_NAME/nodemanager.log" 2>&1 &
NMPID=$!
echo "NodeManager iniciado con PID: $NMPID en la IP $CURRENT_NODE_IP" | tee -a $LOG_FILE


echo "========= Proceso completado exitosamente en $CURRENT_NODE_IP! =========" | tee -a $LOG_FILE
exit 0
