#!/bin/bash

# Configuración
DOMAIN_NAME="OSB_Domain"
JAR_FILE_NAME="OSB_Domain.jar"
LOG_FILE="OSB_Domain.log"
COMMON_DIR="/u01/oracle/product/osb1214/oracle_common/common/bin"
JAVA_HOME="/u01/oracle/product/jdk1.8.0_321/"
DOMAIN_BASE="/filestore"
ADMIN_URL="t3://172.20.212.159:11000"
ADMIN_USER="weblogic"
ADMIN_PASS="weblogic1"
# TODO: Cambiar este enfoque por que detecte la ip de este servwer y esa ip usar en el enroll
NODES=("172.20.212.160" "172.20.212.161")  # Lista de nodos

# Función para manejo de errores
error_handler() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a $LOG_FILE
    exit 1
}

# Verificar archivo JAR
[ -f "/home/weblogic/$JAR_FILE_NAME" ] || error_handler "El archivo jar no se encuentra"

echo "====== Iniciando unpack... ======" | tee -a $LOG_FILE

# Ejecutar unpack
cd "$COMMON_DIR" || error_handler "No se pudo acceder a $COMMON_DIR"

./unpack.sh -domain="$DOMAIN_BASE/$DOMAIN_NAME" \
            -template="/home/weblogic/$JAR_FILE_NAME" \
            -java_home="$JAVA_HOME" \
            -server_start_mode=prod \
            -overwrite_domain=true \
            -log="$LOG_FILE" \
            -log_priority=info || error_handler "Error al ejecutar unpack"

echo "========= Unpack finalizado! =========" | tee -a $LOG_FILE

# Configurar Node Manager
echo "========= Configurando NodeManager =========" | tee -a $LOG_FILE

NM_DIR="$DOMAIN_BASE/$DOMAIN_NAME/nodemanager"

[ -f "$NM_DIR/nodemanager.properties" ] || error_handler "Archivo de propiedades no encontrado"

# Modificar propiedades de NodeManager
sed -i \
    -e 's/SecureListener=true/SecureListener=false/' \
    -e 's/ListenAddress=.*/ListenAddress=0.0.0.0/' \
    "$NM_DIR/nodemanager.properties" || error_handler "Error modificando propiedades"

echo "==== Iniciando NodeManager ====" | tee -a $LOG_FILE
cd "$DOMAIN_BASE/$DOMAIN_NAME/bin" || error_handler "No se pudo acceder a bin/"

# Iniciar NodeManager en background
nohup ./startNodeManager.sh > "$DOMAIN_BASE/$DOMAIN_NAME/nodemanager.log" 2>&1 &
NMPID=$!
echo "NodeManager iniciado con PID: $NMPID" | tee -a $LOG_FILE

# Esperar a que NodeManager esté listo
sleep 10

# Función para enrollar nodos
enroll_node() {
    local NODE_ADDR=$1
    echo "Enrollando nodo $NODE_ADDR..." | tee -a $LOG_FILE
    
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
        error_handler "Error al enrollar nodo $NODE_ADDR"
    fi
    
    echo "Nodo $NODE_ADDR enrollado exitosamente" | tee -a $LOG_FILE
}

# Enrollar cada nodo
for NODE in "${NODES[@]}"; do
    enroll_node "$NODE"
done

# Detener NodeManager (opcional, dependiendo de tu flujo)
kill $NMPID

echo "========= Proceso completado exitosamente! =========" | tee -a $LOG_FILE
exit 0