#!/bin/bash

DOMAIN_NAME="PostventaEAI_001"
JAR_FILE_NAME="PostventaEAI_001.jar"
UNPACK_FILE="unpack.sh"
COMMON_DIR="/u01/oracle/product/wls12214/oracle_common/common/bin"
DOMAIN_DIR="/u01/oracle/domains"
NODE_USER="weblogic"
NODE_PASSWORD="weblogic1"  
LOG_FILE="/var/log/deploy_$(date +%Y%m%d).log"

NODES=("172.17.116.14" "172.17.116.15")

if ! command -v sshpass &> /dev/null; then
    echo "ERROR: sshpass no está instalado. Instálalo con:"
    echo "  sudo yum install sshpass -y   # Para RHEL/CentOS"
    echo "  sudo apt-get install sshpass  # Para Ubuntu/Debian"
    exit 1
fi

error_acceso_directorio() {
    echo "Error: ($?) $1" | tee -a $LOG_FILE
    exit 1
}

run_remote() {
    local node_ip=$1
    local command=$2
    sshpass -p "$NODE_PASSWORD" ssh -o StrictHostKeyChecking=no -o LogLevel=ERROR \
        "$NODE_USER@$node_ip" "$command"
}

transfer_file() {
    local node_ip=$1
    local src_file=$2
    local dest_path=$3
    sshpass -p "$NODE_PASSWORD" scp -o StrictHostKeyChecking=no -o LogLevel=ERROR \
        "$src_file" "$NODE_USER@$node_ip:$dest_path"
}

echo '===== Iniciando el enpaquetado..... =====' | tee -a $LOG_FILE
cd "$COMMON_DIR" || error_acceso_directorio "No se pudo acceder a $COMMON_DIR"

./pack.sh -domain="$DOMAIN_DIR/$DOMAIN_NAME" -template="$DOMAIN_DIR/$JAR_FILE_NAME" \
    -managed=true -template_name="$DOMAIN_NAME" >> "$LOG_FILE" 2>&1 || {
    error_acceso_directorio "Falló el pack.sh"
}

echo '==== Copiando el pack generado =====' | tee -a $LOG_FILE
cd "$DOMAIN_DIR" || error_acceso_directorio "No se pudo acceder a $DOMAIN_DIR"
cp "$JAR_FILE_NAME" "/home/weblogic/" || {
    error_acceso_directorio "No se pudo copiar $JAR_FILE_NAME"
}

deploy_to_node() {
    local NODE_IP=$1
    
    echo "[$(date '+%H:%M:%S')] Procesando nodo: $NODE_IP" | tee -a $LOG_FILE
    
    echo "==== Transfiriendo pack al nodo $NODE_IP ====" | tee -a $LOG_FILE
    for file in "$JAR_FILE_NAME" "$UNPACK_FILE"; do
        if ! transfer_file "$NODE_IP" "/home/weblogic/$file" "/home/weblogic/"; then
            echo "ERROR: Falló transferencia de $file a $NODE_IP" | tee -a $LOG_FILE
            return 1
        fi
    done
    
    echo "==== Iniciando unpack en $NODE_IP ====" | tee -a $LOG_FILE
    if ! run_remote "$NODE_IP" "
        chmod +x /home/weblogic/$UNPACK_FILE && \
        cd /home/weblogic && \
        ./$UNPACK_FILE
    "; then
        echo "ERROR: Falló el unpack en $NODE_IP" | tee -a $LOG_FILE
        return 1
    fi
    
    echo "==== Proceso completado en $NODE_IP ====" | tee -a $LOG_FILE
    return 0
}

if [ ! -f "/home/weblogic/$JAR_FILE_NAME" ]; then
    error_acceso_directorio "El archivo $JAR_FILE_NAME no existe en /home/weblogic"
fi

declare -A pids
for NODE_IP in "${NODES[@]}"; do
    deploy_to_node "$NODE_IP" &
    pids["$NODE_IP"]=$!
done

status=0
for NODE_IP in "${!pids[@]}"; do
    wait "${pids[$NODE_IP]}" || {
        echo "ERROR: Falló el despliegue en $NODE_IP" | tee -a $LOG_FILE
        status=1
    }
done

if [ $status -eq 0 ]; then
    echo "Despliegue completado exitosamente en TODOS los nodos: $(date)" | tee -a $LOG_FILE
else
    echo "ALERTA: Hubo errores en uno o más nodos" | tee -a $LOG_FILE
    exit 1
fi